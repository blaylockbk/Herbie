"""
Inventory (index file) parsing for Herbie v2.

Supported formats
-----------------
wgrib2      ``<msg>:<byte>:<ref_time>:<var>:<level>:<fxx>[:…]``
eccodes     Newline-delimited JSON (ECMWF open data)
directory   HTML directory listing  (Canadian MSC / Navy)

Public API
----------
read_index(source, style, *, source_url, ...) → pl.DataFrame
create_download_groups(df) → pl.DataFrame
generate_index(grib_path) → str | None
generate_index_file(grib_path, overwrite) → Path | None
"""

from __future__ import annotations

import logging
import re
import subprocess
from io import StringIO
from pathlib import Path
from shutil import which
from collections.abc import Callable

import polars as pl
import requests

_WGRIB2 = which("wgrib2")
_FRONT_COLS = ["grib_message", "start_byte", "end_byte", "reference_time", "source"]
_WGRIB2_FIXED = [
    "grib_message",
    "start_byte",
    "reference_time",
    "variable",
    "level",
    "forecast_time",
]
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetch_raw(source) -> str:
    if isinstance(source, StringIO):
        return source.getvalue()
    s = str(source)
    if not s.startswith("http"):
        return Path(source).read_text()
    resp = requests.get(s, timeout=30)
    resp.raise_for_status()
    return resp.text


def _reorder(df: pl.DataFrame) -> pl.DataFrame:
    front = [c for c in _FRONT_COLS if c in df.columns]
    rest = [c for c in df.columns if c not in front]
    return df.select(front + rest)


def _drop_empty_cols(df: pl.DataFrame) -> pl.DataFrame:
    """Remove columns that are entirely null or entirely empty strings."""
    keep = []
    for c in df.columns:
        if c in _FRONT_COLS:
            keep.append(c)
            continue
        col = df[c]
        all_null = col.null_count() == df.height
        all_empty = col.dtype == pl.String and (col.is_null() | (col == "")).all()
        if not all_null and not all_empty:
            keep.append(c)
    return df.select(keep)


# ---------------------------------------------------------------------------
# wgrib2 parser
# ---------------------------------------------------------------------------


def _read_wgrib2(raw: str, source_url: str) -> pl.DataFrame:
    rows: list[list[str]] = []
    for line in raw.strip().splitlines():
        parts = line.rstrip(":").split(":")
        if len(parts) >= 3:
            rows.append(parts)

    if not rows:
        raise ValueError("wgrib2 index is empty or unparseable.")

    n_fixed = len(_WGRIB2_FIXED)
    max_cols = max(len(r) for r in rows)
    extra = (
        [f"field_{i}" for i in range(max_cols - n_fixed)] if max_cols > n_fixed else []
    )
    col_names = (_WGRIB2_FIXED + extra)[:max_cols]
    rows_padded = [r + [""] * (max_cols - len(r)) for r in rows]

    raw_df = pl.DataFrame(
        {col: [r[i] for r in rows_padded] for i, col in enumerate(col_names)}
    )

    start_i64 = raw_df["start_byte"].cast(pl.Int64)

    df = raw_df.with_columns(
        pl.col("grib_message").cast(pl.Int64),
        start_i64.alias("start_byte"),
        (start_i64.shift(-1) - 1).alias("end_byte"),
        pl.col("reference_time")
        .str.strip_chars()
        .str.pad_end(14, "0")
        .str.to_datetime("d=%Y%m%d%H%M", strict=False)
        .alias("reference_time"),
        pl.lit(source_url).alias("source"),
    )

    return _reorder(_drop_empty_cols(df))


# ---------------------------------------------------------------------------
# ecCodes parser
# ---------------------------------------------------------------------------


def _read_eccodes(raw: str, source_url: str) -> pl.DataFrame:
    import json

    records = [json.loads(l) for l in raw.strip().splitlines() if l.strip()]
    if not records:
        raise ValueError("ecCodes index is empty or unparseable.")

    df = pl.DataFrame(records)

    df = (
        df.with_row_index(name="grib_message", offset=1)
        .with_columns(
            start_byte=pl.col("_offset").cast(pl.Int64),
            end_byte=(pl.col("_offset") + pl.col("_length")).cast(pl.Int64),
            reference_time=pl.concat_str(
                [pl.col("date"), pl.col("time"), pl.lit("00")]
            ).str.to_datetime("%Y%m%d%H%M%S", strict=False),
            forecast_time=pl.duration(
                hours=pl.col("step").cast(pl.Int64, strict=False)
            ),
            source=pl.lit(source_url),
        )
        .drop(["_offset", "_length", "date", "time", "step"])
    )

    df = df[[c for c in df.columns if df[c].null_count() < df.height]]
    return _reorder(df)


# ---------------------------------------------------------------------------
# Directory listing parser
# ---------------------------------------------------------------------------


def _read_directory(
    url: str,
    pattern: str,
    parse_metadata: Callable | None,
) -> pl.DataFrame:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"Could not fetch directory listing from {url}: {exc}"
        ) from exc

    regex = re.compile(pattern)
    rows: list[dict] = []

    for match in regex.finditer(resp.text):
        meta: dict = match.groupdict()
        fname = meta.pop("filename", match.group(0))
        if parse_metadata:
            meta.update(parse_metadata(fname))
        meta["filename"] = fname
        meta["url"] = url.rstrip("/") + "/" + fname
        meta["source"] = url
        rows.append(meta)

    return pl.DataFrame(rows) if rows else pl.DataFrame()


# ---------------------------------------------------------------------------
# wgrib2 local fallback
# ---------------------------------------------------------------------------


def generate_index(grib_path) -> str | None:
    """Run ``wgrib2 -s`` on a local file; return the text, or None if unavailable."""
    if not _WGRIB2:
        return None
    result = subprocess.run(
        [_WGRIB2, "-s", str(grib_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"wgrib2 failed (code {result.returncode}):\n{result.stderr}"
        )
    return result.stdout


def generate_index_file(grib_path, overwrite: bool = False) -> "Path | None":
    """Write ``<grib_path>.idx`` via wgrib2; return its path or None."""
    grib_path = Path(grib_path)
    idx_path = Path(str(grib_path) + ".idx")
    if idx_path.exists() and not overwrite:
        return idx_path
    text = generate_index(grib_path)
    if text is None:
        return None
    idx_path.write_text(text)
    return idx_path


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def read_index(
    source,
    style: str = "wgrib2",
    *,
    source_url: str = "",
    directory_pattern: str = "",
    parse_metadata: Callable | None = None,
) -> pl.DataFrame:
    """
    Read a GRIB2 index and return a tidy Polars DataFrame.

    Parameters
    ----------
    source
        URL, local path, StringIO, or directory URL.
    style
        ``'wgrib2'``, ``'eccodes'``, ``'directory'``, or ``'auto'``.
    source_url
        URL/path of the associated GRIB2 data file (stored in ``source`` column).
    directory_pattern
        Regex pattern (``style='directory'`` only).
    parse_metadata
        Optional ``(filename) → dict`` callable (``style='directory'`` only).
    """
    if style == "directory":
        return _read_directory(str(source), directory_pattern, parse_metadata)

    raw = _fetch_raw(source)
    url = source_url or str(source)

    if style == "wgrib2":
        return _read_wgrib2(raw, url)
    if style == "eccodes":
        return _read_eccodes(raw, url)
    if style == "auto":
        try:
            return _read_wgrib2(raw, url)
        except Exception:
            return _read_eccodes(raw, url)
    raise ValueError(
        f"Unknown style {style!r}. Use 'wgrib2', 'eccodes', 'directory', or 'auto'."
    )


def create_download_groups(df: pl.DataFrame) -> pl.DataFrame:
    """
    Collapse consecutive GRIB messages into byte-range download groups.

    Consecutive messages (grib_message numbers differing by 1) sharing
    the same ``source`` are merged into a single range request.
    """
    if df.is_empty():
        return df

    result = (
        df.sort("grib_message")
        .with_columns(
            download_group=(
                (pl.col("grib_message").diff().fill_null(1) != 1)
                .cum_sum()
                .cast(pl.Int32)
            ),
        )
        .group_by("source", "download_group", maintain_order=True)
        .agg(
            pl.col("start_byte").min(),
            pl.when(pl.col("end_byte").is_null().any())
            .then(pl.lit(None))
            .otherwise(pl.col("end_byte").max())
            .alias("end_byte"),
            pl.col("*").exclude("source", "download_group", "start_byte", "end_byte"),
        )
        .sort("download_group")
    )

    total = (result["end_byte"] - result["start_byte"]).sum()
    log.debug(
        "Grouped %d messages → %d groups (%s bytes)",
        len(df),
        len(result),
        f"{total:,}" if total else "unknown",
    )
    return result

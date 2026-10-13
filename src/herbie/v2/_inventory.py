"""
Inventory (index file) parsing for Herbie v2.

Supported formats
-----------------
wgrib2      ``<msg>:<byte>:<ref_time>:<var>:<level>:<step>[:…]``
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
# Local index generation  (wgrib2 or eccodes fallback)
# ---------------------------------------------------------------------------


def _generate_wgrib2_idx(grib_path: Path, idx_path: Path) -> "Path | None":
    """Run ``wgrib2 -s`` and write the output to *idx_path*."""
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
            "wgrib2 failed (code {}):{}{}".format(
                result.returncode, "\n", result.stderr
            )
        )
    idx_path.write_text(result.stdout)
    return idx_path


def _generate_eccodes_idx(grib_path: Path, idx_path: Path) -> "Path | None":
    """
    Iterate GRIB messages with the ``eccodes`` Python library and write a
    wgrib2-compatible ``.idx`` text file.

    The output uses eccodes ``shortName`` for the variable column, which is
    consistent with ecCodes key conventions and ideal for IFS/ECMWF files.
    The resulting file is parseable by ``read_index(..., style='wgrib2')``.
    """
    try:
        import eccodes
    except ImportError:
        raise ImportError(
            "The eccodes Python package is required for index_fallback_method='eccodes'. "
            "Install it with: pip install eccodes  (or via cfgrib)"
        ) from None

    lines: list[str] = []
    with open(grib_path, "rb") as fh:
        msg_num = 0
        while True:
            h = eccodes.codes_grib_new_from_file(fh)
            if h is None:
                break
            msg_num += 1
            try:

                def _get(key, default="", _h=h):  # noqa: E306  (default captures h by value)
                    try:
                        return eccodes.codes_get(_h, key)
                    except eccodes.CodesInternalError:
                        return default

                offset = _get("offset", 0)
                date_str = str(_get("dataDate", ""))
                time_str = str(int(_get("dataTime", 0))).zfill(4)
                ref_time = "d={}{}".format(date_str, time_str)
                short_name = _get("shortName", "UNKNOWN")
                type_level = _get("typeOfLevel", "unknown")
                level = _get("level", 0)
                step = str(_get("stepRange", "anl"))
                lines.append(
                    "{}:{}:{}:{}:{}:{}:{}:".format(
                        msg_num, offset, ref_time, short_name, type_level, level, step
                    )
                )
            finally:
                eccodes.codes_release(h)

    idx_path.write_text("\n".join(lines) + "\n")
    return idx_path


def generate_local_index(
    grib_path,
    method: str = "auto",
    overwrite: bool = False,
) -> "Path | None":
    """
    Generate a local ``.idx`` index file alongside *grib_path*.

    Writes ``<grib_path>.idx`` and returns its path.  If the file already
    exists and *overwrite* is ``False``, returns the existing path immediately
    without invoking the backend.

    Parameters
    ----------
    grib_path
        Path to the local GRIB2 file.
    method
        ``"auto"``    — use wgrib2 if it is on ``PATH``, otherwise eccodes.
        ``"wgrib2"``  — require wgrib2; raises ``RuntimeError`` if not found.
        ``"eccodes"`` — use the ``eccodes`` Python library.
    overwrite
        Re-generate even if ``<grib_path>.idx`` already exists.

    Returns
    -------
    Path | None
        Path to the written ``.idx`` file, or ``None`` on failure.
    """
    grib_path = Path(grib_path)
    idx_path = Path(str(grib_path) + ".idx")

    if idx_path.exists() and not overwrite:
        return idx_path

    resolved = method
    if method == "auto":
        resolved = "wgrib2" if _WGRIB2 else "eccodes"
    elif method == "wgrib2" and not _WGRIB2:
        raise RuntimeError(
            "index_fallback_method='wgrib2' requested but wgrib2 is not on PATH."
        )

    log.debug("Generating local index for %s via %s", grib_path.name, resolved)

    if resolved == "wgrib2":
        return _generate_wgrib2_idx(grib_path, idx_path)
    if resolved == "eccodes":
        return _generate_eccodes_idx(grib_path, idx_path)
    raise ValueError(
        "Unknown index_fallback_method {!r}. Use 'auto', 'wgrib2', or 'eccodes'.".format(
            method
        )
    )


# ---------------------------------------------------------------------------
# Backward-compatible wrappers  (pre-v2 API)
# ---------------------------------------------------------------------------


def generate_index(grib_path) -> "str | None":
    """Run ``wgrib2 -s`` on a local file; return the text, or ``None``."""
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
            "wgrib2 failed (code {}):{}{}".format(
                result.returncode, "\n", result.stderr
            )
        )
    return result.stdout


def generate_index_file(grib_path, overwrite: bool = False) -> "Path | None":
    """Write ``<grib_path>.idx`` via wgrib2; return its path or ``None``.

    .. deprecated::
        Use :func:`generate_local_index` with ``method='wgrib2'`` instead.
    """
    return generate_local_index(grib_path, method="wgrib2", overwrite=overwrite)


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

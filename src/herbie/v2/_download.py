"""
Download engine for Herbie v2.

Handles both full-file downloads and byte-range subset downloads.
Uses ThreadPoolExecutor for parallel subset fetching and Rich for
progress display.

Public API
----------
download_file(url, dest, *, verbose)
    Download a complete remote file.

download_groups(df, dest, *, max_workers, verbose)
    Download a set of byte-range groups (subset download) in parallel
    and concatenate them into a single output file.
"""

from __future__ import annotations

import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock

import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

import polars as pl

console = Console()


# ---------------------------------------------------------------------------
# Full-file download
# ---------------------------------------------------------------------------


def download_file(
    url: str,
    dest: Path,
    *,
    chunk_size: int = 8192,
    verbose: bool = True,
) -> Path:
    """Stream a complete file from *url* to *dest*."""
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))

    dest.parent.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=True,
        disable=not verbose,
    ) as progress:
        task = progress.add_task(f"[cyan]Downloading {dest.name}", total=total or None)

        with open(dest, "wb") as fh:
            for chunk in response.iter_content(chunk_size=chunk_size):
                fh.write(chunk)
                progress.update(task, advance=len(chunk))

    return dest


# ---------------------------------------------------------------------------
# Byte-range fetch helpers
# ---------------------------------------------------------------------------


def _fetch_local_range(
    path: Path,
    start: int,
    end: int | None,
    tmp: Path,
    chunk_size: int = 65536,
) -> Path:
    with open(path, "rb") as src, open(tmp, "wb") as dst:
        src.seek(start)
        remaining = (end - start + 1) if end is not None else None
        while True:
            read_size = (
                min(chunk_size, remaining) if remaining is not None else chunk_size
            )
            data = src.read(read_size)
            if not data:
                break
            dst.write(data)
            if remaining is not None:
                remaining -= len(data)
                if remaining <= 0:
                    break
    return tmp


def _fetch_remote_range(
    url: str,
    start: int,
    end: int | None,
    tmp: Path,
    chunk_size: int = 65536,
) -> Path:
    end_str = str(end) if end is not None else ""
    headers = {"Range": f"bytes={start}-{end_str}"}
    resp = requests.get(url, headers=headers, stream=True, timeout=60)
    resp.raise_for_status()

    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"Server returned HTTP {resp.status_code}; range requests may not be supported. "
            "Try downloading the full file first: H.download()"
        )

    with open(tmp, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            fh.write(chunk)
    return tmp


def _fetch_group(
    source: str,
    start: int,
    end: int | None,
    group_id: int,
    tmp_dir: Path,
    progress: Progress,
    lock: Lock,
) -> tuple[int, Path]:
    """Fetch one byte-range group. Called from a thread pool."""
    tmp = tmp_dir / f"group_{group_id:06d}.part"
    total = (end - start + 1) if end is not None else None

    with lock:
        task = progress.add_task(f"[yellow]group {group_id:04d}", total=total)

    try:
        is_local = not source.startswith(("http://", "https://"))
        if is_local:
            _fetch_local_range(Path(source), start, end, tmp)
        else:
            _fetch_remote_range(source, start, end, tmp)

        with lock:
            progress.update(task, completed=total or 0)
            progress.remove_task(task)

        return group_id, tmp

    except Exception:
        with lock:
            try:
                progress.remove_task(task)
            except Exception:
                pass
        raise


# ---------------------------------------------------------------------------
# Subset download (parallel)
# ---------------------------------------------------------------------------


def download_groups(
    df: pl.DataFrame,
    dest: Path,
    *,
    max_workers: int = 5,
    verbose: bool = True,
) -> Path:
    """
    Download byte-range groups in parallel and concatenate into *dest*.

    Parameters
    ----------
    df
        DataFrame from ``create_download_groups()``.  Must have columns:
        ``source``, ``start_byte``, ``end_byte``, ``download_group``.
    dest
        Output file path.
    max_workers
        Maximum concurrent download threads.
    verbose
        Show progress bars.
    """
    timer = datetime.now()
    dest.parent.mkdir(parents=True, exist_ok=True)

    tasks = [
        {
            "source": row["source"],
            "start": int(row["start_byte"]),
            "end": int(row["end_byte"]) if row["end_byte"] is not None else None,
            "group_id": int(row["download_group"]),
        }
        for row in df.iter_rows(named=True)
    ]

    if not tasks:
        raise ValueError("No download groups to process.")

    results: dict[int, Path] = {}
    lock = Lock()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
            refresh_per_second=10,
            transient=True,
            disable=not verbose,
        ) as progress:
            overall = progress.add_task("[bold cyan]Overall", total=len(tasks))

            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(
                        _fetch_group,
                        t["source"],
                        t["start"],
                        t["end"],
                        t["group_id"],
                        tmp_path,
                        progress,
                        lock,
                    ): t["group_id"]
                    for t in tasks
                }

                for future in as_completed(futures):
                    group_id, tmp_file = future.result()  # raises on error
                    results[group_id] = tmp_file
                    progress.update(overall, advance=1)

        # Concatenate in order
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
            disable=not verbose,
        ) as progress:
            task = progress.add_task("[cyan]Writing output", total=len(results))
            with open(dest, "wb") as out:
                for gid in sorted(results):
                    out.write(results[gid].read_bytes())
                    progress.update(task, advance=1)

    elapsed = (datetime.now() - timer).total_seconds()
    if verbose:
        console.print(
            f"[bold green]✓ Done[/bold green] ({elapsed:.1f}s) → [yellow]{dest}[/yellow]"
        )

    return dest

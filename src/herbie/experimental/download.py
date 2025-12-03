"""Download helpers for GRIB2 subset downloading."""

import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any
from collections.abc import Generator

import requests
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

from ._common import console, logger


def index_source_to_grib_source(source: str) -> str | None:
    """Return the GRIB2 file source from an index file source.

    Handles common index suffixes.
    """
    for suffix in (".idx", ".inv", ".index"):
        if source.endswith(suffix):
            return source.removesuffix(suffix)
    return None


def _read_local_byte_range(
    source_path: Path,
    start_byte: int,
    end_byte: int,
    temp_file: Path,
    chunk_size: int = 8192,
) -> Generator[int, None, None]:
    """Read a byte range from a local file.

    Yields
    ------
        Number of bytes read in each chunk for progress tracking
    """
    byte_count = end_byte - start_byte + 1

    with open(source_path, "rb") as src:
        src.seek(start_byte)

        remaining = byte_count
        with open(temp_file, "wb") as dst:
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                chunk = src.read(read_size)
                if not chunk:
                    break
                dst.write(chunk)
                remaining -= len(chunk)
                yield len(chunk)


def _download_remote_byte_range(
    url: str,
    start_byte: int,
    end_byte: int,
    temp_file: Path,
    chunk_size: int = 8192,
) -> Generator[int, None, None]:
    """Download a byte range from a remote URL.

    Yields
    ------
        Number of bytes downloaded in each chunk for progress tracking.

    Raises
    ------
        Exception: If server doesn't support range requests
    """
    headers = {
        "Range": f"bytes={start_byte}-{end_byte if end_byte is not None else ''}"
    }

    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()

    if response.status_code != 206:
        raise Exception(
            f"Server doesn't support range requests (status: {response.status_code})"
        )

    with open(temp_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            yield len(chunk)


def download_byte_range(
    source: str | Path,
    start_byte: int,
    end_byte: int,
    download_group: int,
    temp_dir: Path,
    progress: Progress,
    progress_lock: Lock,
) -> tuple[int, Path]:
    """Download/extract a specific byte range from a source and save to a temporary file.

    Args:
        source: Either a URL (str starting with http:// or https://) or a local file path
        start_byte: Starting byte position
        end_byte: Ending byte position
        download_group: Group identifier for the download
        temp_dir: Directory to store temporary files
        progress: Progress bar instance
        progress_lock: Lock for thread-safe progress updates

    Returns
    -------
        Tuple of (download_group, temp_file_path)
    """
    # Determine if source is local or remote
    is_local = isinstance(source, Path) or (
        isinstance(source, str) and not source.startswith(("http://", "https://"))
    )

    temp_file = temp_dir / f"group_{download_group:04d}.grib2"

    with progress_lock:
        task_id = progress.add_task(f"[yellow]Group {download_group:04d}", total=None)

    try:
        if is_local:
            total_size = end_byte - start_byte + 1
            reader = _read_local_byte_range(
                Path(source),
                start_byte,
                end_byte,
                temp_file,
            )
        else:
            # For remote, we'll get total from response headers
            # Set total to None initially, will be updated on first chunk
            total_size = end_byte - start_byte + 1 if end_byte is not None else None
            reader = _download_remote_byte_range(
                source,
                start_byte,
                end_byte,
                temp_file,
            )

        with progress_lock:
            progress.update(task_id, total=total_size)

        for bytes_processed in reader:
            with progress_lock:
                progress.update(task_id, advance=bytes_processed)

        with progress_lock:
            progress.remove_task(task_id)

        return (download_group, temp_file)

    except Exception as e:
        with progress_lock:
            # Ensure task removed to avoid stale bar
            try:
                progress.remove_task(task_id)
            except Exception:
                pass
        logger.error(f"Error processing group {download_group}: {e}")
        raise


def download_grib2_from_dataframe(
    df: Any, output_file: str | Path, max_workers: int = 5
) -> Path:
    """Download GRIB2 data from a polars DataFrame with byte ranges.

    `df` should have columns: source, download_group, start_byte, end_byte
    """
    timer = datetime.now()
    output_file = Path(output_file).resolve()

    logger.debug(f"Download {len(df)} groups with maximum {max_workers} workers.")

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Prepare download tasks
        download_tasks = []
        for row in df.iter_rows(named=True):
            grib_source = index_source_to_grib_source(row["source"])
            download_tasks.append(
                {
                    "source": grib_source,
                    "start_byte": row["start_byte"],
                    "end_byte": row["end_byte"],
                    "download_group": row["download_group"],
                }
            )

        # Download all groups in parallel with progress tracking
        results = {}
        progress_lock = Lock()

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
        ) as progress:
            # Create overall progress task
            overall_task = progress.add_task(
                "[bold cyan]Overall Progress", total=len(download_tasks)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}

                for task in download_tasks:
                    future = executor.submit(
                        download_byte_range,
                        task["source"],
                        task["start_byte"],
                        task["end_byte"],
                        task["download_group"],
                        temp_path,
                        progress,
                        progress_lock,
                    )
                    futures[future] = task["download_group"]

                # Wait for completion
                for future in as_completed(futures):
                    try:
                        group_num, temp_file = future.result()
                        results[group_num] = temp_file
                        progress.update(overall_task, advance=1)
                    except Exception as e:
                        logger.error(f"Download failed: {e}")
                        raise
            # Progress context is transient; no need to remove overall task

        # Concatenate files in order
        logger.debug("Concatenating downloaded groups into a single file.")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            transient=True,
        ) as progress:
            concat_task = progress.add_task(
                "[cyan]Writing output file", total=len(results)
            )

            with open(output_file, "wb") as outfile:
                for group_num in sorted(results.keys()):
                    temp_file = results[group_num]
                    with open(temp_file, "rb") as infile:
                        outfile.write(infile.read())
                    progress.update(concat_task, advance=1)

        logger.debug(f"Subset file written to {output_file}.")
        timer_seconds = (datetime.now() - timer).total_seconds()
        logger.info(
            f"[bold green]Download complete![/bold green] time={timer_seconds:.0f}s Output saved to: {output_file}"
        )
        return output_file

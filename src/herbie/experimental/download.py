"""Download helpers for GRIB2 subset downloading."""

import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any

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


def download_byte_range(
    source: str,
    start_byte: int,
    end_byte: int,
    download_group: int,
    temp_dir: Path,
    progress: Progress,
    progress_lock: Lock,
) -> tuple[int, Path]:
    """Download a specific byte range from a source and save to a temporary file."""
    headers = {
        "Range": f"bytes={start_byte}-{end_byte if end_byte is not None else ''}"
    }
    temp_file = temp_dir / f"group_{download_group:04d}.grib2"

    # Create progress bar for this download
    with progress_lock:
        task_id = progress.add_task(f"[yellow]Group {download_group:04d}", total=None)

    try:
        response = requests.get(source, headers=headers, stream=True)
        response.raise_for_status()

        # Check if server supports range requests
        if response.status_code == 206:
            total_size = int(response.headers.get("content-length", 0))

            with progress_lock:
                progress.update(task_id, total=total_size)

            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    with progress_lock:
                        progress.update(task_id, advance=len(chunk))

            # Remove the progress bar when complete
            with progress_lock:
                progress.remove_task(task_id)

            return (download_group, temp_file)
        else:
            with progress_lock:
                progress.remove_task(task_id)
            raise Exception(
                f"Server doesn't support range requests (status: {response.status_code})"
            )

    except Exception as e:
        with progress_lock:
            # Ensure task removed to avoid stale bar
            try:
                progress.remove_task(task_id)
            except Exception:
                pass
        logger.error(f"Error downloading group {download_group}: {e}")
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

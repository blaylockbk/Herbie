"""Process index files to create inventories."""

import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polars as pl
import requests


def read_wgrib2_index(source) -> pl.DataFrame:
    """Parse wgrib2-style index files as inventory DataFrames with Polars."""
    df = (
        pl.read_csv(
            source,
            has_header=False,
            separator=":",
            new_columns=[
                "grib_message",
                "start_byte",
                "reference_time",
                "variable",
                "level",
                "forecast_time",
            ],
        )
        .with_columns(
            pl.col("reference_time")
            .str.pad_end(14, "0")
            .str.to_datetime("d=%Y%m%d%H%M")
        )
        .insert_column(2, (pl.col("start_byte").shift(-1) - 1).alias("end_byte"))
        .insert_column(
            3,
            pl.concat_str(
                pl.col("start_byte"),
                pl.lit("-"),
                pl.col("end_byte").cast(pl.String).fill_null(""),
            ).alias("byte_range"),
        )
        .insert_column(0, pl.lit(source).alias("url"))
    )

    # Drop column with all nulls
    df = df[[s.name for s in df if not (s.null_count() == df.height)]]

    return df


def download_groups(df) -> pl.DataFrame:
    """Get download groups from a filtered Inventory DataFrame."""
    return (
        df.with_columns(
            download_group=(pl.col("grib_message").diff().fill_null(1) != 1).cum_sum(),
        )
        .group_by("url", "download_group", maintain_order=True)
        .agg(
            pl.col("start_byte").min(),
            pl.col("end_byte").max(),
            pl.col("grib_message"),
            pl.col("variable"),
            pl.col("level"),
        )
        .insert_column(
            3,
            pl.concat_str(
                pl.col("start_byte"),
                pl.lit("-"),
                pl.col("end_byte").cast(pl.String).fill_null(""),
            ).alias("byte_range"),
        )
    )


# ======================================================================
# From Claude Below
# ======================================================================


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def download_byte_range(
    url: str, start_byte: int, end_byte: int, download_group: int, temp_dir: Path
) -> tuple[int, Path]:
    """
    Download a specific byte range from a URL and save to a temporary file.

    Args:
        url: The source URL (without .idx suffix)
        start_byte: Starting byte position
        end_byte: Ending byte position
        download_group: Group number for ordering
        temp_dir: Directory to save temporary files
    """
    # Remove .idx suffix if present
    if url.endswith(".idx"):
        url = url[:-4]

    # Create byte range header
    headers = {"Range": f"bytes={start_byte}-{end_byte}"}

    temp_file = temp_dir / f"group_{download_group:04d}.grib2"

    try:
        logger.info(
            f"Downloading group {download_group}: bytes {start_byte}-{end_byte}"
        )
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()

        # Check if server supports range requests
        if response.status_code == 206:
            with open(temp_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Group {download_group} downloaded successfully")
            return (download_group, temp_file)
        else:
            raise Exception(
                f"Server doesn't support range requests (status: {response.status_code})"
            )

    except Exception as e:
        logger.error(f"Error downloading group {download_group}: {e}")
        raise


def download_grib2_from_dataframe(
    df: pl.DataFrame, output_file: str, max_workers: int = 5
) -> None:
    """
    Download GRIB2 data from a polars DataFrame with byte ranges.

    Args:
        df: Polars DataFrame with columns: url, download_group, start_byte, end_byte
        output_file: Path to the final output file
        max_workers: Number of concurrent download threads
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        logger.info(f"Using temporary directory: {temp_path}")

        # Prepare download tasks
        download_tasks = []
        for row in df.iter_rows(named=True):
            download_tasks.append(
                {
                    "url": row["url"],
                    "start_byte": row["start_byte"],
                    "end_byte": row["end_byte"],
                    "download_group": row["download_group"],
                }
            )

        # Download all groups in parallel
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    download_byte_range,
                    task["url"],
                    task["start_byte"],
                    task["end_byte"],
                    task["download_group"],
                    temp_path,
                ): task["download_group"]
                for task in download_tasks
            }
            for future in as_completed(futures):
                try:
                    group_num, temp_file = future.result()
                    results[group_num] = temp_file
                except Exception as e:
                    logger.error(f"Download failed: {e}")
                    raise

        # Concatenate files in order
        logger.info("Concatenating downloaded files...")
        with open(output_file, "wb") as outfile:
            for group_num in sorted(results.keys()):
                temp_file = results[group_num]
                logger.info(f"Appending group {group_num} to output file")
                with open(temp_file, "rb") as infile:
                    outfile.write(infile.read())

        logger.info(f"Download complete! Output saved to: {output_file}")


if __name__ == "__main__":
    from herbie import Herbie

    H = Herbie("2025-11-01")
    df = read_wgrib2_index(H.idx).filter(pl.col("variable").is_in(["UGRD", "VGRD"]))
    df = download_groups(df)

    # Download the GRIB2 data
    download_grib2_from_dataframe(
        df=df,
        output_file="output.grib2",
        max_workers=5,  # Adjust based on your network and CPU
    )

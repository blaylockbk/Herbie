"""Process index files to create inventories."""

import polars as pl

from ._common import logger, IndexStyle, InventoryDataFrame, DownloadGroupDataFrame


def _sort_columns(df: pl.DataFrame) -> pl.DataFrame:
    return df.select(
        [
            "source",
            "index",
            "start_byte",
            "end_byte",
            "reference_time",
            *[
                col
                for col in df.columns
                if col
                not in {
                    "source",
                    "index",
                    "start_byte",
                    "end_byte",
                    "reference_time",
                }
            ],
        ]
    )


def _read_wgrib2_index(source) -> InventoryDataFrame:
    """Parse wgrib2-style index files as inventory DataFrames."""
    logger.info(f"Reading index file: {source}")
    df = pl.read_csv(
        source,
        has_header=False,
        separator=":",
        new_columns=[
            "index",
            "start_byte",
            "reference_time",
            "variable",
            "level",
            "forecast_time",
        ],
    ).with_columns(
        source=pl.lit(source),
        end_byte=(pl.col("start_byte").shift(-1) - 1),
        reference_time=pl.col("reference_time")
        .str.pad_end(14, "0")
        .str.to_datetime("d=%Y%m%d%H%M"),
    )

    # Drop column with all nulls
    df = df[[s.name for s in df if not (s.null_count() == df.height)]]

    df = df.pipe(_sort_columns)

    logger.debug(f"Loaded {len(df)} records from the wgrib2-style index file.")
    return df


def _read_eccodes_index(source) -> InventoryDataFrame:
    """Parse wgrib2-style index files as inventory DataFrames."""
    df = (
        pl.read_ndjson(source)
        .with_columns(
            source=pl.lit(str(source)),
            reference_time=pl.concat_str(
                [pl.col("date"), pl.col("time"), pl.lit("00")]
            ).str.to_datetime("%Y%m%d%H%M%S"),
            forecast_time=pl.duration(hours=pl.col("step").cast(int)),
            start_byte=pl.col("_offset"),
            end_byte=(pl.col("_offset") + pl.col("_length")),
        )
        .drop("date", "time", "step", "_offset", "_length")
        .with_row_index(name="index", offset=1)
    )

    # Drop column with all nulls
    df = df[[s.name for s in df if not (s.null_count() == df.height)]]

    df = df.pipe(_sort_columns)

    logger.debug(f"Loaded {len(df)} records from the ecCodes-style index file.")

    return df


def read_index_file(source, style: IndexStyle | None = None) -> InventoryDataFrame:
    """
    Read a GRIB2 index file; either wgrib2 or eccodes style.

    Args:
        source: Path or URL to the index file
        style: Index file style ("wgrib2" or "eccodes"). If None, tries both.
    """
    if style == "wgrib2":
        return _read_wgrib2_index(source)
    elif style == "eccodes":
        return _read_eccodes_index(source)
    elif style is None:
        try:
            return _read_wgrib2_index(source)
        except Exception as e1:
            try:
                return _read_eccodes_index(source)
            except Exception as e2:
                raise ValueError(
                    f"Failed to load index file '{source}'\n"
                    f"  wgrib2-style : {e1}\n"
                    f"  eccodes-style: {e2}"
                )
    else:
        raise ValueError(f"Unknown index style: {style}. Must be 'wgrib2' or 'eccodes'")


def create_download_groups(df: InventoryDataFrame) -> DownloadGroupDataFrame:
    """Get download groups from a filtered Inventory DataFrame."""
    result = (
        df.with_columns(
            download_group=(pl.col("index").diff().fill_null(1) != 1).cum_sum(),
        )
        .group_by("source", "grib_source", "download_group", maintain_order=True)
        .agg(
            pl.col("start_byte").min(),
            pl.when(pl.col("end_byte").is_null().any())
            .then(pl.lit(None))
            .otherwise(pl.col("end_byte").max())
            .alias("end_byte"),
            pl.col("*").exclude("start_byte", "end_byte"),
        )
    )

    # Calculate total bytes
    total_bytes = (result["end_byte"] - result["start_byte"]).sum()
    logger.debug(
        f"Grouped {len(df)} messages into {len(result)} download groups ({total_bytes:,} bytes total)"
    )

    return result

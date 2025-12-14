"""
Inventory utilities for reading and parsing GRIB2 index files.

This module contains functions for reading, parsing, and filtering GRIB2
inventory index files created by wgrib2 or eccodes.
"""

import json
import warnings
from io import StringIO
from pathlib import Path
from typing import Literal

import pandas as pd
import requests


def read_index_file(
    idx: str | Path | StringIO,
    idx_source: str,
    idx_style: Literal["wgrib2", "eccodes"] = "wgrib2",
    verbose: bool = False,
) -> str:
    """
    Read the contents of an index file.

    Parameters
    ----------
    idx : str, Path, or StringIO
        The index file location (URL, file path, or StringIO object)
    idx_source : str
        The source of the index file ('local', 'generated', or remote URL)
    idx_style : {'wgrib2', 'eccodes'}
        The style of index file
    verbose : bool
        Print verbose output

    Returns
    -------
    str
        The contents of the index file
    """
    if idx_source in ["local", "generated"]:
        if isinstance(idx, StringIO):
            return idx.read()
        else:
            return Path(idx).read_text()
    else:
        if verbose:
            print(f"Downloading inventory file from {idx=}")
        try:
            response = requests.get(idx)
            response.raise_for_status()
        except Exception as e:
            raise ValueError(
                f"\nCant open index file {idx}\n"
                f"Download the full file first (with `H.download()`).\n"
                f"You will need to remake the Herbie object (H = `Herbie()`)\n"
                f"or delete this cached property: `del H.index_as_dataframe()`"
            ) from e
        else:
            content = response.text
            response.close()
            return content


def save_index_file(
    content: str,
    index_filepath: Path,
) -> None:
    """
    Save index file content to disk.

    Parameters
    ----------
    content : str
        The index file content to save
    index_filepath : Path
        The path where the index file should be saved
    """
    index_filepath = Path(index_filepath)
    index_filepath.parent.mkdir(parents=True, exist_ok=True)
    index_filepath.write_text(content)


def parse_wgrib2_index(
    content: str,
    fxx: int,
) -> pd.DataFrame:
    """
    Parse a wgrib2-style index file into a DataFrame.

    Parameters
    ----------
    content : str
        The content of the wgrib2 index file
    fxx : int
        The forecast hour

    Returns
    -------
    pd.DataFrame
        Parsed index file as a DataFrame
    """
    df = pd.read_csv(
        StringIO(content),
        sep=":",
        names=[
            "grib_message",
            "start_byte",
            "reference_time",
            "variable",
            "level",
            "forecast_time",
            "?",
            "??",
            "???",
        ],
    )

    # Format the DataFrame
    df["reference_time"] = pd.to_datetime(df.reference_time, format="d=%Y%m%d%H")
    df["valid_time"] = df["reference_time"] + pd.to_timedelta(f"{fxx}h")
    df["start_byte"] = df["start_byte"].astype(int)
    df["end_byte"] = df["start_byte"].shift(-1) - 1
    df["range"] = df.apply(
        lambda x: f"{x.start_byte:.0f}-{x.end_byte:.0f}".replace("nan", ""),
        axis=1,
    )
    df = df.reindex(
        columns=[
            "grib_message",
            "start_byte",
            "end_byte",
            "range",
            "reference_time",
            "valid_time",
            "variable",
            "level",
            "forecast_time",
            "?",
            "??",
            "???",
        ]
    )

    df = df.dropna(how="all", axis=1)

    df["search_this"] = (
        df.loc[:, "variable":]
        .astype(str)
        .apply(
            lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
            axis=1,
        )
    )

    return df


def parse_eccodes_index(
    content: str,
) -> pd.DataFrame:
    """
    Parse an eccodes-style index file into a DataFrame.

    Parameters
    ----------
    content : str
        The content of the eccodes index file

    Returns
    -------
    pd.DataFrame
        Parsed index file as a DataFrame
    """
    idxs = [json.loads(x) for x in content.split("\n") if x]
    df = pd.DataFrame(idxs)

    # Format the DataFrame
    df.index = df.index.rename("grib_message")
    df.index += 1
    df = df.reset_index()
    df["start_byte"] = df["_offset"]
    df["end_byte"] = df["_offset"] + df["_length"]
    df["range"] = df.start_byte.astype(str) + "-" + df.end_byte.astype(str)
    df["reference_time"] = pd.to_datetime(df.date + df.time, format="%Y%m%d%H%M")
    df["step"] = pd.to_timedelta(df.step.astype(int), unit="h")
    df["valid_time"] = df.reference_time + df.step

    df = df.reindex(
        columns=[
            "grib_message",
            "start_byte",
            "end_byte",
            "range",
            "reference_time",
            "valid_time",
            "step",
            # ---- Used for search ------------------------------
            "param",  # parameter field (variable)
            "levelist",  # level
            "levtype",  # sfc=surface, pl=pressure level, pt=potential vorticity
            "number",  # model number (used in ensemble products)
            "domain",  # g=global
            "expver",  # experiment version
            "class",  # classification (od=routing operations, rd=research, )
            "type",  # fc=forecast, an=analysis,
            "stream",  # oper=operationa, wave=wave, ef/enfo=ensemble,
        ]
    )

    df["search_this"] = (
        df.loc[:, "param":]
        .astype(str)
        .apply(
            lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
            axis=1,
        )
    )

    return df


def filter_inventory(
    df: pd.DataFrame,
    search: str | None = None,
    verbose: bool = False,
    idx_style: Literal["wgrib2", "eccodes"] = "wgrib2",
) -> pd.DataFrame:
    """
    Filter inventory DataFrame by a search string.

    Parameters
    ----------
    df : pd.DataFrame
        The inventory DataFrame to filter
    search : str, optional
        Regular expression string to filter GRIB messages.
        If None or ":", returns the full DataFrame.
    verbose : bool
        Print warning if no messages found
    idx_style : {'wgrib2', 'eccodes'}
        The style of index file (for help messages)

    Returns
    -------
    pd.DataFrame
        Filtered inventory DataFrame
    """
    from herbie.help import _search_help

    if search not in [None, ":"]:
        logic = df.search_this.str.contains(search)
        if (logic.sum() == 0) and verbose:
            print(
                f"No GRIB messages found. There might be something wrong with {search=}"
            )
            print(_search_help(kind=idx_style))
        df = df.loc[logic]

    return df


def add_inventory_attributes(
    df: pd.DataFrame,
    idx: str | Path,
    idx_source: str,
    model: str,
    product: str,
    fxx: int,
    date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Add metadata attributes to the inventory DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The inventory DataFrame
    idx : str or Path
        The index file location
    idx_source : str
        The source of the index file
    model : str
        The model name
    product : str
        The product name
    fxx : int
        The forecast hour
    date : pd.Timestamp
        The initialization datetime

    Returns
    -------
    pd.DataFrame
        DataFrame with added attributes
    """
    df.attrs = dict(
        url=idx,
        source=idx_source,
        description="Inventory index file for the GRIB2 file.",
        model=model,
        product=product,
        lead_time=fxx,
        datetime=date,
    )
    return df


def create_inventory_from_wgrib2(
    grib_file: Path,
    fxx: int,
    model: str,
    product: str,
    date: pd.Timestamp,
) -> pd.DataFrame:
    """
    Generate inventory from a GRIB2 file using wgrib2.

    Parameters
    ----------
    grib_file : Path
        Path to the GRIB2 file
    fxx : int
        The forecast hour
    model : str
        The model name
    product : str
        The product name
    date : pd.Timestamp
        The initialization datetime

    Returns
    -------
    pd.DataFrame
        Generated inventory DataFrame
    """
    from herbie.core import wgrib2_idx

    if not wgrib2_idx:
        raise RuntimeError(
            "wgrib2 is required to generate index files but was not found."
        )

    content = wgrib2_idx(grib_file)
    df = parse_wgrib2_index(content, fxx)
    df = add_inventory_attributes(
        df,
        idx=None,
        idx_source="generated",
        model=model,
        product=product,
        fxx=fxx,
        date=date,
    )

    return df

"""Reading and deciphering GRIB index files.

TODO:
- [ ] Need to create a "search_this" column for each DataFrame type.
- [ ] Need to compute byte range for each GRIB message.
- [ ] Need to include companion GRIB file (remote and/or local)
- [ ] Need to include GRIB expected file size.
- [ ] Need to include searchString hash.
"""

import functools
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from herbie.help import _searchString_help
from herbie.misc import ANSI


def get_grib_filesize(grib_filepath):
    """Get the size of the GRIB file size in bytes."""
    if str(grib_filepath).startswith("http"):
        grib_filesize = int(
            requests.get(grib_filepath, stream=True).headers["Content-Length"]
        )
    else:
        grib_filesize = Path(grib_filepath).stat().st_size

    return grib_filesize


def read_wgrib2_index(index_filepath):
    """Read and format a wgrib2-style index file as a DataFrame.

    Parameters
    ----------
    index_filepath : str or path object
        The file path or URL to a wgrib2-styel index file.
    """
    grib_filepath, index_suffix = index_filepath.rsplit(".", 1)

    try:
        grib_filesize = get_grib_filesize(grib_filepath)
    except Exception:
        grib_filesize = np.nan

    df = pd.read_csv(
        index_filepath,
        sep=":",
        header=None,
        names=[
            "grib_message",
            "start_byte",
            "datetime",
            "variable",
            "level",
            "lead",
            "?",
            "??",
            "???",
            "????",
            "?????",
            "??????",
            "???????",
        ],
    ).dropna(how="all", axis=1)

    df["datetime"] = pd.to_datetime(df["datetime"], format="d=%Y%m%d%H")

    df["start_byte"] = df["start_byte"].astype(int)
    df["end_byte"] = df["start_byte"].shift(-1, fill_value=grib_filesize + 1) - 1
    df["bytes"] = df["end_byte"] - df["start_byte"]
    df["range"] = df.apply(
        lambda x: f"{x['start_byte']:.0f}-{x['end_byte']:.0f}".replace("nan", ""),
        axis=1,
    )

    column_order = [
        "grib_message",
        "start_byte",
        "end_byte",
        "bytes",
        "range",
        "datetime",
        "variable",
        "level",
        "lead",
    ]
    remaining_columns = [i for i in df.columns if i not in column_order]

    df = df.reindex(columns=column_order + remaining_columns)
    df["search_this"] = (
        df.loc[:, "variable":]
        .astype(str)
        .apply(
            lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
            axis=1,
        )
    )
    df.attrs["index_filepath"] = index_filepath
    df.attrs["index_suffix"] = index_suffix
    df.attrs["index_style"] = "wgrib2"
    df.attrs["grib_filepath"] = grib_filepath
    df.attrs["grib_filesize"] = grib_filesize

    return df


def read_eccodes_index(index_filepath):
    """Read and format an eccodes-style index file as a DataFrame.

    The eccodes keywords are explained here:
    https://confluence.ecmwf.int/display/UDOC/Identification+keywords

    Parameters
    ----------
    index_filepath : str or path object
        The file path or URL to a eccodes-style index file.
    """
    grib_filepath, index_suffix = index_filepath.rsplit(".", 1)

    try:
        grib_filesize = get_grib_filesize(grib_filepath)
    except Exception:
        grib_filesize = np.nan

    df = pd.read_json(index_filepath, lines=True)
    df = df.rename(
        columns={
            "step": "lead",
            "param": "variable",
            "levelist": "level",
            "levtype": "level_type",
            "_offset": "start_byte",
            "_length": "bytes",
        }
    )

    df["datetime"] = pd.to_datetime(
        df["date"].astype(str) + " " + df["time"].astype(str).str.zfill(2)
    )
    df = df.drop(columns=["date", "time"])
    df["lead"] = pd.to_timedelta(df["lead"].astype(int), unit="H")
    df["valid_time"] = df["datetime"] + df["lead"]
    df["end_byte"] = df["start_byte"] + df["bytes"] - 1
    df["range"] = df.apply(
        lambda x: f"{x['start_byte']:.0f}-{x['end_byte']:.0f}".replace("nan", ""),
        axis=1,
    )
    df["grib_message"] = np.arange(df.shape[0]) + 1

    column_order = [
        "grib_message",
        "start_byte",
        "end_byte",
        "bytes",
        "range",
        "datetime",
        "valid_time",
        "lead",
        # ---- Used for searchString ------------------------------
        "variable",  # parameter field (variable)
        "level",  # level
        "level_type",  # sfc=surface, pl=pressure level, pt=potential vorticity
        "number",  # model number (only used in ensemble products)
        "domain",  # g=global
        "expver",  # experiment version
        "class",  # classification (od=routing operations, rd=research, )
        "type",  # fc=forecast, an=analysis,
        "stream",  # oper=operationa, wave=wave, ef/enfo=ensemble,
    ]
    remaining_columns = [i for i in df.columns if i not in column_order]

    df = df.reindex(columns=column_order + remaining_columns)

    df["search_this"] = (
        df.loc[:, "variable":]
        .astype(str)
        .apply(
            lambda x: ":" + ":".join(x).rstrip(":").replace(":nan:", ":"),
            axis=1,
        )
    )

    df.attrs["index_filepath"] = index_filepath
    df.attrs["index_suffix"] = index_suffix
    df.attrs["index_style"] = "eccodes"
    df.attrs["grib_filepath"] = grib_filepath
    df.attrs["grib_filesize"] = grib_filesize

    return df


class Inventory:
    """Inventory of GRIB file contents."""

    def __init__(self, index_filepath):
        self.index_filepath = index_filepath
        self.grib_filepath, self.index_suffix = index_filepath.rsplit(".", 1)

    @functools.cached_property
    def dataframe(self):
        """Load the index file into a Pandas DataFrame."""
        try:
            df = read_wgrib2_index(self.index_filepath)
            self.style = "wgrib2"
        except Exception as wgrib2_failed:
            try:
                df = read_eccodes_index(self.index_filepath)
                self.style = "eccodes"
            except Exception as eccodes_failed:
                raise ValueError(
                    f"Could not read index file.\n\n"
                    f"read_wgrib2_index failed because: {wgrib2_failed}\n\n"
                    f"read_eccodes_index failed because: {eccodes_failed}"
                )
        return df

    def filter(self, searchString=None):
        """Filter the Inventory DataFrame for specific GRIB messages.

        Parameters
        ----------
        searchString : str
            A regular expression string to filter specific GRIB messages
            in the inventory DataFrame.

            Read more in the user guide at
            https://herbie.readthedocs.io/en/latest/user_guide/searchString.html
        """
        # Filter DataFrame by searchString
        if searchString not in [None, ":"]:
            logic = self.dataframe["search_this"].str.contains(searchString)
            if logic.sum() == 0:
                print(
                    f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
                    f" │ WARNING: No GRIB messages found with                 │\n"
                    f" │ `searchString='{searchString:50s}'`.       │\n"
                    f" │ Try a different searchString.                        │\n"
                    f" ╰──────────────────────────────────────────────────────╯\n"
                )
                print(_searchString_help(style=self.style))

            filtered_df = self.dataframe.loc[logic].copy()
        else:
            filtered_df = self.dataframe.copy()

        # Create column "download_group" which tels us which grib messages
        # are adjacent to each other in the file.
        filtered_df["download_group"] = filtered_df.grib_message.diff().ne(1).cumsum()

        return filtered_df

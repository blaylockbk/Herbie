"""Read and decipher GRIB index files.

GRIB index files are an ASCII file that describe the contents of a GRIB2
file. The come in two flavors: (1) wgrib2 and (2) eccodes. Index files
may be a local file path (like a Path object) or on a remote server and
accessible via http or https.

In Herbie terminology, an "index" file refers to the actual index file
produced by wgrib2 or eccodes. The "Inventory" is a representation of
the index contents in a Pandas DataFrame, which may contain additional
data derived from the index content, but not explicitly given.

TODO: Parsing info from an index file needs to be as fast as possible.
"""

import functools
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from herbie.help import _searchString_help
from herbie.misc import ANSI


def get_grib_filesize(grib_filepath):
    """Get the size of a GRIB file in bytes."""
    if str(grib_filepath).startswith("http"):
        if requests.head(grib_filepath).status_code < 400:
            grib_filesize = int(
                requests.get(grib_filepath, stream=True).headers["Content-Length"]
            )
        else:
            raise FileNotFoundError(f"The GRIB file is not found: {grib_filepath}")
    else:
        if Path(grib_filepath).exists():
            grib_filesize = Path(grib_filepath).stat().st_size
        else:
            raise FileNotFoundError(f"The GRIB file is not found: {grib_filepath}")

    return grib_filesize


def read_wgrib2_index(index_filepath):
    """Read and format a wgrib2-style index file as an Inventory DataFrame.

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
    """Read and format an eccodes-style index file as an Inventory DataFrame.

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
    """Inventory of GRIB file contents.

    It is assumed that the GRIB file described by the index file exists
    in the same location.

    Parameters
    ----------
    index_filepath : str or path object
        Path or URL of an index file.

    Examples
    --------
    >>> I = Inventory("/path/to/myFile.grib2.idx")
    >>> I.dataframe
    >>> I.filter("UGRD|VGRD")
    """

    def __init__(self, index_filepath):
        self.index_filepath = index_filepath
        if not self._index_exists():
            raise FileNotFoundError(
                f"The index file does not exist: {self.index_filepath}."
            )

        self.grib_filepath, self.index_suffix = index_filepath.rsplit(".", 1)

        if not self._grib_exists():
            # If the GRIB filepath does exist, maybe try checking for the
            # file with a different suffix...
            self.grib_filepath += ".grib2"
            if not self._grib_exists():
                raise FileNotFoundError(
                    f"The GRIB file but does not exist: {self.grib_filepath}."
                )

    def _index_exists(self):
        """Check if the index file exists."""
        if str(self.index_filepath).startswith("http"):
            return requests.head(self.index_filepath).status_code < 400
        else:
            return Path(self.index_filepath).exists()

    def _grib_exists(self):
        """Check if the GRIB file exists."""
        if str(self.grib_filepath).startswith("http"):
            return requests.head(self.grib_filepath).status_code < 400
        else:
            return Path(self.grib_filepath).exists()

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
                    f"read_wgrib2_index() failed because: {wgrib2_failed}\n\n"
                    f"read_eccodes_index() failed because: {eccodes_failed}"
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
                msg = f"`searchString='{searchString}'`"
                print(
                    f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
                    f" │ WARNING: No GRIB messages found with                 │\n"
                    f" │ {msg:52s} │\n"
                    f" │ Try a different searchString.                        │\n"
                    f" ╰──────────────────────────────────────────────────────╯"
                )
                print(_searchString_help(style=self.style))

            filtered_df = self.dataframe.loc[logic].copy()
        else:
            filtered_df = self.dataframe.copy()

        # Create column "download_group" which tels us which grib messages
        # are adjacent to each other in the file.
        filtered_df["download_group"] = filtered_df.grib_message.diff().ne(1).cumsum()

        return filtered_df

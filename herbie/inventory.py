"""Reading and deciphering GRIB index files."""

import functools

import pandas as pd

from herbie.help import _searchString_help


def read_wgrib2_index(FILE):
    """Read and format a wgrib2-style index file as a DataFrame.

    Parameters
    ----------
    FILE : path or str
        The file path or URL to a wgrib2-styel index file.
    """
    df = pd.read_csv(
        FILE,
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
        ],
    ).dropna(axis=1)
    df["datetime"] = pd.to_datetime(df["datetime"], format="d=%Y%m%d%H")

    return df


def read_eccodes_index(FILE):
    """Read and format an eccodes-style index file as a DataFrame.

    The eccodes keywords are explained here:
    https://confluence.ecmwf.int/display/UDOC/Identification+keywords

    Parameters
    ----------
    FILE : path or str
        The file path or URL to a wgrib2-styel index file.
    """
    df = pd.read_json(FILE, lines=True).rename(
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
    return df


class Inventory:
    """Inventory of GRIB file contents."""

    def __init__(self, index_file):
        self.index_file = index_file

    @functools.cached_property
    def dataframe(self):
        """Load the index file into a Pandas DataFrame."""
        try:
            df = read_wgrib2_index(self.index_file)
            self.kind = "wgrib2"
        except Exception as wgrib2_failed:
            try:
                df = read_eccodes_index(self.index_file)
                self.kind = "eccodes"
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
            logic = self.dataframe['search_this'].str.contains(searchString)
            if logic.sum() == 0:
                print(
                    f"No GRIB messages found with `searchString='{searchString}'`. Try a different searchString."
                )
                print(_searchString_help(kind=self.kind))
            return self.dataframe.loc[logic]
        else:
            return self.dataframe

"""Reading and deciphering GRIB index files."""

from io import StringIO

import pandas as pd
import requests


def read_wgrib2_index(FILE):
    """Read a wgrib2-style index file as a DataFrame."""
    if not str(FILE).startswith("http"):
        # Index file should be a local ASCII file.
        read_this = FILE
    else:
        # Index file is on a remote server.
        response = requests.get(FILE)
        if response.status_code != 200:
            response.raise_for_status()
            response.close()
            raise ValueError(
                f"\nCan't open index file {FILE}\n"
                f"Download the full file first (with `H.download()`).\n"
                f"You will need to remake the Herbie object (H = `Herbie()`)\n"
                f"or delete this cached property: `del H.index_as_dataframe()`"
            )
        read_this = StringIO(response.text)
        response.close()

    df = pd.read_csv(
        read_this,
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
    return df


def read_eccodes_index():
    """Read a eccodes-style index file as a DataFrame."""
    pass


class Inventory:
    """Inventory of GRIB file contents."""

    def __init__(self, index_file):
        self.index_file = index_file

    def filter(self, searchString):
        """Filter the Inventory DataFrame for specific GRIB messages."""
        pass

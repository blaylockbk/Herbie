## Nikhil Shankar
## August 10, 2025

"""
Tests for downloading HRDPS model.

DRAGONS:

At ~00Z the HRDPS servers are cleared of the previous day's forecasts.
The next forecast arrives at ~06Z. During the interim period these tests will fail.
"""

from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)
yesterday = today - timedelta(days=1)
yesterday_12z = yesterday.replace(hour=12, minute=0)
today_str = today.strftime("%Y-%m-%d %H:%M")
yesterday_12z_str = yesterday_12z.strftime("%Y-%m-%d %H:%M")

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

# Remove all previous test data
for i in (save_dir / "hrdps").rglob("*"):
    if i.is_file():
        i.unlink()


def test_hrdps_download():
    H = Herbie(
        yesterday_12z,
        model="hrdps",
        product="continental",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    assert H
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


def test_hrdps_north_download():
    H = Herbie(
        yesterday_12z,
        model="hrdps",
        product="north",
        variable="RH",
        level="ISBL_0550",
        overwrite=True,
        save_dir=save_dir,
    )
    assert H
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


def test_hrdps_xarray():
    H = Herbie(
        yesterday,
        model="hrdps",
        product="continental",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    assert H
    H.xarray(remove_grib=False)
    assert H.get_localFilePath().exists()
    H.get_localFilePath().unlink()

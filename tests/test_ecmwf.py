"""Tests for downloading ECMWF model."""

from datetime import datetime, timedelta

import pytest

from herbie import Herbie, config

now = datetime.now() - timedelta(hours=12)
yesterday = datetime(now.year, now.month, now.day)
today_str = yesterday.strftime("%Y-%m-%d %H:%M")
save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

DATES = [
    datetime(2024, 1, 31),  # older 0.4 degree IFS data
    datetime(2024, 2, 26),  # newer 0.25 degree IFS data
    yesterday,  # Test yesterdays' data
]

FILTERS = [
    ":10(?:u|v):",  # 10 meter wind variables
    ":t:",  # temperature at all levels
]


@pytest.mark.parametrize("date", DATES)
def test_ifs_download(date):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)

    # Test full file download
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


@pytest.mark.parametrize("date", DATES)
def test_ifs_download_partial(date):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)
    f = H.download(":2t:")
    assert H.get_localFilePath(":2t:").exists()
    f.unlink()


@pytest.mark.parametrize("date, filter", [(d, f) for d in DATES for f in FILTERS])
def test_ifs_xarray(date, filter):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)
    H.xarray(filter, remove_grib=False)
    assert H.get_localFilePath(filter).exists()
    H.get_localFilePath(filter).unlink()


def test_aifs_yesterday():
    H = Herbie(yesterday, model="aifs", save_dir=save_dir, overwrite=True)
    H.xarray(":10(?:u|v):")

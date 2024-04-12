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
]


@pytest.mark.parametrize("date", DATES)
def test_ifs_download(date):
    H = Herbie(
        date,
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test full file download
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


@pytest.mark.parametrize("date", DATES)
def test_ifs_download_partial(date):
    H = Herbie(
        date,
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test partial file download
    # temperature at all levels
    f = H.download(":t:")
    assert H.get_localFilePath(":t:").exists()
    f.unlink()


@pytest.mark.parametrize("date", DATES)
def test_ifs_xarray(date):
    H = Herbie(
        date,
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )
    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()


def test_ifs_yesterday():
    H = Herbie(
        yesterday,
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test full file download
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()

    # Test partial file download
    # temperature at all levels
    f = H.download(":t:")
    assert H.get_localFilePath(":t:").exists()
    f.unlink()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()


def test_aifs_yesterday():
    H = Herbie(
        yesterday,
        model="aifs",
        save_dir=save_dir,
    )

    # Test full file download
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()

    # Test partial file download
    # temperature at all levels
    f = H.download(":t:")
    assert H.get_localFilePath(":t:").exists()
    f.unlink()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()

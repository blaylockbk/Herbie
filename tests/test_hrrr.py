## Brian Blaylock
## October 13, 2021

"""
Tests for downloading HRRR model
"""
from datetime import datetime, timedelta
from shutil import which

import pytest

from herbie import Herbie, Path
import os
import requests
import pandas as pd

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)
yesterday = today - timedelta(days=1)
today_str = today.strftime("%Y-%m-%d %H:%M")
yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M")
save_dir = Path("$TMPDIR/Herbie-Tests/").expand()

# Location of wgrib2 command, if it exists
wgrib2 = which("wgrib2")


def test_hrrr_aws1():
    # Test HRRR with datetime.datetime date
    H = Herbie(
        today,
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
    )
    H.download()
    assert H.get_localFilePath().exists()
    H.xarray("TMP:2 m", remove_grib=False)
    assert H.get_localFilePath("TMP:2 m").exists()


def test_hrrr_to_netcdf():
    """Check that a xarray Dataset can be written to a NetCDF file."""
    H = Herbie(
        "2022-01-01 06:00",
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
    )
    ds = H.xarray("TMP:2 m", remove_grib=False)
    ds.to_netcdf(save_dir / "test_hrrr_to_netcdf.nc")


def test_hrrr_aws2():
    # Test HRRR with string date
    H = Herbie(
        yesterday_str,
        model="hrrr",
        product="prs",
        save_dir=save_dir,
    )
    H.xarray("(?:U|V)GRD:10 m")

    if os.name != "nt":
        # If not windows (nt), then check that the file was removed.
        # (because windows can't remove an open grib2 file).
        assert not H.get_localFilePath("(?:U|V)GRD:10 m").exists()


def test_do_not_remove_file():
    # Test HRRR with datetime.datetime date
    H = Herbie(
        today,
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
    )
    # Download a subset file
    var = "TMP:2 m"
    H.download(var)
    assert H.get_localFilePath(var).exists()

    # Read with xarray, and try to remove it
    H.xarray(var, remove_grib=True)
    assert H.get_localFilePath(var).exists()


@pytest.mark.skipif(wgrib2 is None, reason="wgrib2 not installed")
def test_make_idx_with_wgrib():
    H = Herbie(
        "2022-12-13 6:00",
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
    )
    H.download(verbose=True)

    # Pretent this was a local file
    H.idx = None
    H.idx_source = None
    H.grib_source = "local"

    # Generate IDX file
    df = H.inventory()
    assert len(df), "Length of index file is 0."
    assert H.idx_source == "generated", "Doesn't look like a generated idx file."


@pytest.mark.skipif(wgrib2 is None, reason="wgrib2 not installed")
def test_create_idx_with_wgrib2():
    """Test that Herbie can make an index file with wgrib2 when an index file is not found"""
    H = Herbie(
        today_str,
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
    )
    H.download()
    H.idx = None
    assert len(H.index_as_dataframe) > 0


# ===========================
# Check Downloaded File Sizes
# ===========================


def test_hrrr_file_size_full():
    """Test that theoretical size matches actual size for full (non-subset) files."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)
    stated_size = int(
        requests.get(H.SOURCES["aws"], stream=True).headers["Content-Length"]
    )
    H.download()
    assert stated_size == H.get_localFilePath().stat().st_size


def test_hrrr_file_size_subset1():
    """Test that the U/V wind components are downloaded correctly."""
    var = ":.GRD:"
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)
    H.download(var)

    idx = H.inventory(var)
    stated_size = ((idx.end_byte + 1) - idx.start_byte).sum()

    assert stated_size == H.get_localFilePath(var).stat().st_size


def test_hrrr_file_size_subset2():
    """Test that the temperatures are downloaded correctly."""
    var = ":TMP:"
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)
    H.download(var)

    idx = H.inventory(var)
    stated_size = ((idx.end_byte + 1) - idx.start_byte).sum()

    assert stated_size == H.get_localFilePath(var).stat().st_size


def test_hrrr_file_size_subset3():
    """Test that same level is downloaded correctly."""
    var = ":500 mb:"
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)
    H.download(var)

    idx = H.inventory(var)
    stated_size = ((idx.end_byte + 1) - idx.start_byte).sum()

    assert stated_size == H.get_localFilePath(var).stat().st_size

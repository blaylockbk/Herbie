## Brian Blaylock
## October 13, 2021

"""
Tests for downloading RAP model
"""
import pandas as pd
import pytest

from herbie import Herbie
from tests.util import is_time_between

today = pd.to_datetime("today").floor("1D") - pd.to_timedelta("1D")
save_dir = "$TMPDIR/Herbie-Tests/"


@pytest.mark.skipif(
    is_time_between("00:00", "02:30"),
    reason="Test hibernated between 00:00 and 02:30 UTC, "
    "because upstream data not available or incomplete at night.",
)
def test_rap_aws():
    # Test
    H = Herbie(
        today,
        model="rap",
        save_dir=save_dir,
    )
    assert H.grib is not None

    # Test downloading the file
    H = Herbie(
        today,
        model="rap",
        save_dir=save_dir,
    )
    H.download()
    assert H.get_localFilePath().exists()

    H.xarray("TMP:2 m", remove_grib=False)
    assert H.get_localFilePath("TMP:2 m").exists()


def test_rap_historical():
    """Search for RAP urls on NCEI that I know exist"""

    H = Herbie(
        "2019-11-23",
        model="rap_historical",
        product="analysis",
        save_dir=save_dir,
    )
    assert H.grib is not None

    H = Herbie(
        "2005-01-01",
        model="rap_historical",
        product="analysis",
        save_dir=save_dir,
    )
    assert H.grib is not None


def test_rap_ncei():
    H = Herbie(
        "2020-03-15",
        model="rap_ncei",
        product="rap-130-13km",
        save_dir=save_dir,
    )
    assert H.grib is not None


# ===========================
# Check Downloaded File Sizes
# ===========================


def test_rap_file_size_subset1():
    """Test that the U/V wind components are downloaded correctly.

    This test is important for the RAP model which uses
    GRIB submessages for storing UGRD and VGRD

    See https://github.com/blaylockbk/Herbie/issues/259
    """
    var = ":.GRD:10 m"
    H = Herbie("2023-12-01", model="rap", save_dir=save_dir, overwrite=True)
    H.download(var)

    idx = H.inventory(var)
    stated_size = ((idx.end_byte + 1) - idx.start_byte).sum()

    assert stated_size == H.get_localFilePath(var).stat().st_size

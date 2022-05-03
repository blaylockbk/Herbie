## Brian Blaylock
## October 13, 2021

"""
Tests for downloading HRRR model
"""
from datetime import datetime, timedelta

from herbie.archive import Herbie

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)
yesterday = today - timedelta(days=1)
today_str = today.strftime("%Y-%m-%d %H:%M")
yesterday_str = yesterday.strftime("%Y-%m-%d %H:%M")


def test_hrrr_aws1():
    # Test HRRR with datetime.datetime date
    H = Herbie(today, model="hrrr", product="sfc", save_dir="$TMPDIR")
    H.download()
    assert H.get_localFilePath().exists()
    H.xarray("TMP:2 m", remove_grib=False)
    assert H.get_localFilePath("TMP:2 m").exists()


def test_hrrr_aws2():
    # Test HRRR with string date
    H = Herbie(yesterday_str, model="hrrr", product="prs", save_dir="$TMPDIR")
    H.xarray("(?:U|V)GRD:10 m")
    assert not H.get_localFilePath("(?:U|V)GRD:10 m").exists()


def test_create_idx_with_wgrib2():
    """Test that Herbie can make an index file with wgrib2 when an index file is not found"""
    H = Herbie(today_str, model="hrrr", product="sfc", save_dir="$TMPDIR")
    H.download()
    H.idx = None
    assert len(H.index_as_dataframe) > 0

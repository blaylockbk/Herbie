## Brian Blaylock
## October 13, 2021

"""
Tests for downloading RAP model
"""
from datetime import datetime

from herbie.archive import Herbie

now = datetime.now()
today = datetime(now.year, now.month, now.day)
today_str = today.strftime("%Y-%m-%d %H:%M")


def test_rap_aws_datetime():
    H = Herbie(today, model="rap", save_dir="$TMPDIR")

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray("TMP:2 m", remove_grib=False)
    assert H.get_localFilePath("TMP:2 m").exists()


def test_rap_aws_strdate():
    H = Herbie(today_str, model="rap", save_dir="$TMPDIR")

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray("TMP:2 m")
    assert not H.get_localFilePath("TMP:2 m").exists()


def test_rap_ncei_strdate():
    H = Herbie(today_str, model="rap_ncei", save_dir="$TMPDIR")

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray("TMP:2 m")
    assert not H.get_localFilePath("TMP:2 m").exists()

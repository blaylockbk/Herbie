## Brian Blaylock
## October 13, 2021

"""
Tests for downloading HRRR model
"""
from datetime import datetime
from os import remove

from herbie.archive import Herbie

now = datetime.now()
today = datetime(now.year, now.month, now.day)
today_str = today.strftime('%Y-%m-%d %H:%M')

def test_hrrr_aws_datetime():
    H = Herbie(today, model='hrrr', product='sfc', save_dir='$TMPDIR')

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray('TMP:2 m', remove_grib=False)
    assert H.get_localFilePath('TMP:2 m').exists()


def test_hrrr_aws_strdate():
    H = Herbie(today_str, model='hrrr', product='prs', save_dir='$TMPDIR')

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray('TMP:2 m')
    assert not H.get_localFilePath('TMP:2 m').exists()

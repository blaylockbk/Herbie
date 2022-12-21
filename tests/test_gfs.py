## Brian Blaylock
## February 9, 2022

"""
Tests for downloading GFS model
"""

from datetime import datetime, timedelta

from herbie import Herbie

now = datetime.now()
today = datetime(now.year, now.month, now.day) - timedelta(hours=12)
today_str = today.strftime("%Y-%m-%d %H:%M")

save_dir = "$TMPDIR/Herbie-Tests/"


def test_gfs():
    H = Herbie(
        today,
        priority="aws",
        product="pgrb2.0p25",
        model="gfs",
        save_dir="$TMPDIR/Herbie-Tests/",
    )

    assert H.grib, "GFS grib2 file not found"
    assert H.idx, "GFS index file not found"

    H.download()
    assert H.get_localFilePath().exists()

    H.xarray("TMP:2 m", remove_grib=False)
    assert H.get_localFilePath("TMP:2 m").exists()

## Brian Blaylock
## February 9, 2022

"""
Tests for downloading GFS model
"""

from herbie import Herbie

save_dir = "$TMPDIR/Herbie-Tests/"


def test_gefs():
    H = Herbie(
        "2023-01-01 06:00",
        model="gefs",
        fxx=12,
        member="mean",
        save_dir=save_dir,
    )

    assert H.grib, "GEFS grib2 file not found"
    assert H.idx, "GEFS index file not found"


def test_gefs_reforecast():
    H = Herbie(
        "2017-03-14",
        model="gefs_reforecast",
        fxx=12,
        member=0,
        variable_level="tmp_2m",
        save_dir=save_dir,
    )

    assert H.grib, "GEFS grib2 file not found"
    assert H.idx, "GEFS index file not found"

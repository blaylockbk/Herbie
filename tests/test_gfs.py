## Brian Blaylock
## February 9, 2022

"""Tests for downloading GFS model."""

from datetime import datetime, timedelta

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day) - timedelta(hours=12)
today_str = today.strftime("%Y-%m-%d %H:%M")

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


def test_gfs():
    H = Herbie(
        today,
        priority="aws",
        product="pgrb2.0p25",
        model="gfs",
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "GFS grib2 file not found"
    assert H.idx, "GFS index file not found"

    filter = ":TMP:2 m"
    f = H.download(filter)
    assert H.get_localFilePath(filter).exists(), "File doesn't exist!"
    f.unlink()

    H.xarray(filter)

def test_graphcast():
    H = Herbie(
        today-timedelta(hours=12),
        priority="aws",
        product="pgrb2.0p25",
        model="graphcast",
        fxx=6,
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "GFS grib2 file not found"
    assert H.idx, "GFS index file not found"
    
    filter = "HGT:500 mb"
    f = H.download(filter)
    assert H.get_localFilePath(filter).exists(), "File doesn't exist!"
    f.unlink()

    H.xarray(filter)

def test_gfs_ncei_historical_anl():
    print(save_dir)

    H = Herbie(
        datetime(2007, 4, 5),
        priority="ncei_historical_analysis",
        product="0.5-degree",
        model="gfs",
        fxx=0,
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "GFS NCEI Historical Analysis grib2 file not found"
    assert H.idx, "GFS NCEI Historical Analysis index file not found"

    filter = "TMP:900 mb"
    f = H.download(filter)
    assert H.get_localFilePath(filter).exists(), "File doesn't exist!"
    f.unlink()

    H.xarray(filter)

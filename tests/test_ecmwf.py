"""Tests for downloading ECMWF model."""

from datetime import datetime, timedelta

from herbie import Herbie

now = datetime.now() - timedelta(hours=12)
yesterday = datetime(now.year, now.month, now.day)
today_str = yesterday.strftime("%Y-%m-%d %H:%M")
save_dir = "$TMPDIR/Herbie-Tests/"

def test_ifs_old_0p4():
    H = Herbie(
        datetime(2024,1,31),
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test full file download
    H.download()
    assert H.get_localFilePath().exists()

    # Test partial file download
    # temperature at all levels
    H.download(":t:")
    assert H.get_localFilePath(":t:").exists()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()

def test_ifs_old_0p25():
    H = Herbie(
        datetime(2024,2,26),
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test full file download
    H.download()
    assert H.get_localFilePath().exists()

    # Test partial file download
    # temperature at all levels
    H.download(":t:")
    assert H.get_localFilePath(":t:").exists()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()

def test_ifs():
    H = Herbie(
        yesterday,
        model="ifs",
        product="oper",
        save_dir=save_dir,
    )

    # Test full file download
    H.download()
    assert H.get_localFilePath().exists()

    # Test partial file download
    # temperature at all levels
    H.download(":t:")
    assert H.get_localFilePath(":t:").exists()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()


def test_aifs():
    H = Herbie(
        yesterday,
        model="aifs",
        save_dir=save_dir,
    )

    # Test full file download
    H.download()
    assert H.get_localFilePath().exists()

    # Test partial file download
    # temperature at all levels
    H.download(":t:")
    assert H.get_localFilePath(":t:").exists()

    # Test partial file xarray
    H.xarray(":10(?:u|v):", remove_grib=False)
    assert H.get_localFilePath(":10(?:u|v):").exists()

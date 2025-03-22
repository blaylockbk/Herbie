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
    yesterday,  # Test yesterdays' data
]

FILTERS = [
    ":10(?:u|v):",  # 10 meter wind variables
    ":t:",  # temperature at all levels
]


@pytest.mark.parametrize("date", DATES)
def test_ifs_download(date):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)

    # Test full file download
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


@pytest.mark.parametrize("date", DATES)
def test_ifs_download_partial(date):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)
    f = H.download(":2t:")
    assert H.get_localFilePath(":2t:").exists()
    f.unlink()


@pytest.mark.parametrize("date, filter", [(d, f) for d in DATES for f in FILTERS])
def test_ifs_xarray(date, filter):
    H = Herbie(date, model="ifs", product="oper", save_dir=save_dir, overwrite=True)
    H.xarray(filter, remove_grib=False)
    assert H.get_localFilePath(filter).exists()
    H.get_localFilePath(filter).unlink()


class TestAIFS:
    """Tests for ECMWF's AIFS model."""

    def test_aifs_yesterday(self):
        """Test downloading AIFS data from yesterday."""
        H = Herbie(
            yesterday,
            model="aifs",
            save_dir=save_dir,
            overwrite=True,
        )

        assert H.grib, "AIFS GRIB file not found"
        assert H.idx, "AIFS index file not found"

        ds = H.xarray(":10(?:u|v):")
        assert len(ds)

    @pytest.mark.parametrize(
        "date",
        (
            datetime(2025, 1, 1),
            datetime(2025, 2, 9, 6),
            datetime(2025, 2, 9, 12),
            datetime(2025, 2, 25, 0),
            datetime(2025, 2, 25, 6),
        ),
    )
    def test_aifs_path_changes(self, date):
        """Test files are valid on dates the paths changed."""
        H = Herbie(
            date,
            model="aifs",
            save_dir=save_dir,
            overwrite=True,
        )
        assert H.grib
        assert H.idx

"""
Tests for downloading Canadian models HRDPS and RDPS model.

Herbie support for Canadian models is a minimal at best. If you would
like to help support this, please let me know in a new issue/PR/or discussion.

DRAGONS:

At ~00Z the HRDPS servers are cleared of the previous day's forecasts.
The next forecast arrives at ~06Z. During the interim period these tests will fail.
"""

import sys
from datetime import datetime, timedelta

import pytest
import requests

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)
yesterday = today - timedelta(days=1)
yesterday_12z = yesterday.replace(hour=12, minute=0)
today_str = today.strftime("%Y-%m-%d %H:%M")
yesterday_12z_str = yesterday_12z.strftime("%Y-%m-%d %H:%M")

hrdps_continental_url = (
    f"https://dd.weather.gc.ca/{yesterday_12z:%Y%m%d}/WXO-DD/model_hrdps/continental"
)
hrdps_north_url = (
    f"https://dd.weather.gc.ca/{yesterday_12z:%Y%m%d}/WXO-DD/model_hrdps/north"
)
rdps_url = f"https://dd.weather.gc.ca/{yesterday_12z:%Y%m%d}/WXO-DD/model_rdps"

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

# Remove all previous test data
for i in (save_dir / "hrdps").rglob("*"):
    if i.is_file():
        i.unlink()


class TestHRDPS:
    @pytest.mark.skipif(
        not requests.head(
            hrdps_continental_url,
            timeout=5,
        ).ok,
        reason=f"{hrdps_continental_url} not reachable",
    )
    def test_hrdps_download(self):
        H = Herbie(
            yesterday_12z,
            model="hrdps",
            product="continental",
            variable="TMP",
            level="AGL-2m",
            overwrite=True,
            save_dir=save_dir,
        )
        assert H
        f = H.download()
        assert H.get_localFilePath().exists()
        f.unlink()

    @pytest.mark.skipif(
        not requests.head(
            hrdps_north_url,
            timeout=5,
        ).ok,
        reason=f"{hrdps_north_url} not reachable",
    )
    def test_hrdps_north_download(self):
        H = Herbie(
            yesterday_12z,
            model="hrdps",
            product="north",
            variable="RH",
            level="ISBL_0550",
            overwrite=True,
            save_dir=save_dir,
        )
        assert H
        f = H.download()
        assert H.get_localFilePath().exists()
        f.unlink()

    @pytest.mark.skipif(
        not requests.head(
            hrdps_continental_url,
            timeout=5,
        ).ok,
        reason=f"{hrdps_continental_url} not reachable",
    )
    def test_hrdps_xarray(self):
        H = Herbie(
            yesterday_12z,
            model="hrdps",
            product="continental",
            variable="TMP",
            level="AGL-2m",
            overwrite=True,
            save_dir=save_dir,
        )
        assert H
        H.xarray(remove_grib=False)
        assert H.get_localFilePath().exists()
        H.get_localFilePath().unlink()


class TestRDPS:
    @pytest.mark.skipif(
        not requests.head(
            rdps_url,
            timeout=5,
        ).ok,
        reason=f"{rdps_url} not reachable",
    )
    def test_rdps_download(self):
        H = Herbie(
            yesterday_12z,
            model="rdps",
            variable="AirTemp",
            level="IsbL-0550",
            overwrite=True,
            save_dir=save_dir,
        )
        assert H
        f = H.download()
        assert H.get_localFilePath().exists()
        f.unlink()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Requires Python > 3.10")
@pytest.mark.skipif(
    not requests.head(
        hrdps_continental_url,
        timeout=5,
    ).ok,
    reason=f"{hrdps_continental_url} not reachable",
)
def test_hrdps_to_netcdf():
    """Check that a xarray Dataset can be written to a NetCDF file.

    It is important that I have haven't put any python objects in the
    xarray Dataset attributes.
    """
    H = Herbie(
        yesterday_12z,
        model="hrdps",
        product="continental",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    assert H
    ds = H.xarray(remove_grib=False)
    ds.to_netcdf(save_dir / "test_hrdps_to_netcdf.nc")

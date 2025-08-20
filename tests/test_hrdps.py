## Nikhil Shankar
## August 10, 2025

"""
Tests for downloading HRDPS model.

DRAGONS:

At ~00Z the HRDPS servers are cleared of the previous day's forecasts.
The next forecast arrives at ~06Z. During the interim period these tests will fail.
"""

from datetime import datetime

import pandas as pd

from herbie import Herbie, config

now = datetime.now()
latest = pd.Timestamp("now").floor("6h") - pd.Timedelta("6h")

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

# Remove all previous test data
for i in (save_dir / "hrdps").rglob("*"):
    if i.is_file():
        i.unlink()


def test_hrdps_download():
    H = Herbie(
        latest,
        model="hrdps",
        product="continental/2.5km",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    f = H.download()
    assert H.get_localFilePath().exists()
    f.unlink()


def test_hrdps_xarray():
    H = Herbie(
        latest,
        model="hrdps",
        product="continental/2.5km",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    H.xarray(remove_grib=False)
    assert H.get_localFilePath().exists()
    H.get_localFilePath().unlink()


def test_hrdps_to_netcdf():
    """Check that a xarray Dataset can be written to a NetCDF file.

    It is important that I have haven't put any python objects in the
    xarray Dataset attributes.
    """
    H = Herbie(
        latest,
        model="hrdps",
        product="continental/2.5km",
        variable="TMP",
        level="AGL-2m",
        overwrite=True,
        save_dir=save_dir,
    )
    ds = H.xarray(remove_grib=False)
    ds.to_netcdf(save_dir / "test_hrdps_to_netcdf.nc")

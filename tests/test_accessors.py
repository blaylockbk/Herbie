"""Tests for Herbie xarray accessors.

Note: See `test_pick_points.py` for testing the pick_points accessor.
"""

from herbie import Herbie
import xarray as xr

def test_crs():
    H = Herbie(
        "2022-12-13 12:00",
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    crs = ds.herbie.crs
    assert crs

def test_to_180():
    z = xr.Dataset({"longitude": [0, 90, 180, 270, 360]})
    z = z.herbie.to_180()
    assert all(z["longitude"] == [0, 90, -180, -90, 0])

def test_to_360():
    z = xr.Dataset({"longitude": [-90, -180, 0, 90, 180]})
    z = z.herbie.to_360()
    assert all(z["longitude"] == [270, 180, 0, 90, 180])

def test_polygon():
    H = Herbie(
        "2022-12-13 12:00",
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    polygons = ds.herbie.polygon
    assert len(polygons) == 2


def test_with_wind():
    ds = Herbie("2024-01-01").xarray("GRD:10 m above").herbie.with_wind()
    assert len(ds) == 4

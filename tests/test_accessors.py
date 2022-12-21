"""
Tests for Herbie xarray accessors
"""

from herbie import Herbie

def test_crs():
    H = Herbie(
        '2022-12-13 12:00',
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    crs = ds.herbie.crs
    assert crs

def test_nearest_points():
    H = Herbie(
        '2022-12-13 12:00',
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    ds1 = ds.herbie.nearest_points([(-100, 40), (-105,35)])
    assert len(ds1.t2m)

def test_polygon():
    H = Herbie(
        '2022-12-13 12:00',
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    polygons = ds.herbie.polygon
    assert len(polygons)==2

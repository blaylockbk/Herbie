"""
Tests for Herbie xarray accessors
"""

from herbie import Herbie
from shapely.geometry import MultiPoint
import pandas as pd


def test_crs():
    H = Herbie(
        "2022-12-13 12:00",
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    crs = ds.herbie.crs
    assert crs


def test_nearest_points():
    ds = Herbie("2022-12-13 12:00", model="hrrr", product="sfc").xarray("TMP:2 m")

    p3 = [(-110, 50), (-100, 40), (-105, 35)]
    n3 = ["AAA", "BBB", "CCC"]

    test_points = [
        (-100, 40),
        [-100, 40],
        p3,
        # MultiPoint(p3), #Only test this if we pin shapely>=2.0
        pd.DataFrame(p3, columns=["longitude", "latitude"], index=n3),
    ]

    for p in test_points:
        ds1 = ds.herbie.nearest_points(p)
        assert len(ds1.t2m)


def test_polygon():
    H = Herbie(
        "2022-12-13 12:00",
        model="hrrr",
        product="sfc",
    )
    ds = H.xarray("TMP:2 m")
    polygons = ds.herbie.polygon
    assert len(polygons) == 2

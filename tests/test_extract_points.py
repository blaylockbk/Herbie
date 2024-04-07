"""Test the ds.herbie.extrac_points() accessor."""

import pandas as pd
import xarray as xr

from herbie import Herbie

ds1 = Herbie("2024-03-01 00:00", model="hrrr").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds2 = Herbie("2024-03-01 00:00", model="hrrr").xarray("[U|V]GRD:10 m")
ds3 = Herbie("2024-03-01 00:00", model="gfs").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds4 = Herbie("2024-03-01 00:00", model="gfs").xarray("[U|V]GRD:10 m")


def test_extract_points():
    """Basic test of Extract Points accessor."""
    points = pd.DataFrame(
        {
            "longitude": [-100, -105, -98.4],
            "latitude": [40, 29, 42.3],
            "stid": ["aa", "bb", "cc"],
        }
    )
    for ds in [ds1, ds2]:
        x1 = ds.herbie.extract_points(points, method="nearest")
        xw = ds.herbie.extract_points(points, method="weighted")
        x4 = ds.herbie.extract_points(points, method="nearest", k=4)
        x8 = ds.herbie.extract_points(points, method="weighted", k=8)


def test_extract_points_simple():
    """Test a very simple grid."""
    ds = xr.Dataset(
        {"a": (["latitude", "longitude"], [[1, 0], [0, 0]])},
        coords={
            "latitude": (["latitude"], [45, 46]),
            "longitude": (["longitude"], [100, 101]),
        },
    )
    point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]})

    p = ds.herbie.extract_points(point, method="nearest", k=1)
    assert all(
        [
            p.latitude == 45,
            p.longitude == 100,
            p.point_grid_distance.round(2) == 34.02,
            p.point_latitude == 45.25,
            p.point_longitude == 100.25,
            p.a == 1,
        ]
    )


def test_extract_points_self_points():
    """Test extract points with model's own grid points."""
    pass


def test_caching_tree():
    """Test the BallTree caching works as expected."""
    pass

"""Test the ds.herbie.extrac_points() accessor."""

import pandas as pd
import pytest
import xarray as xr
import random
import string
import numpy as np
from herbie import Herbie

ds1 = Herbie("2024-03-01 00:00", model="hrrr").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds2 = Herbie("2024-03-01 00:00", model="hrrr").xarray("[U|V]GRD:10 m above")
ds3 = Herbie("2024-03-01 00:00", model="gfs").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds4 = Herbie("2024-03-01 00:00", model="gfs").xarray("[U|V]GRD:10 m above")


def generate_random_string(len=8):
    """Generate a random string."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=len))


@pytest.mark.parametrize("ds", [ds1, ds2, ds3, ds4])
def test_pick_points(ds):
    """Test pick_points accessor on real data."""
    points = pd.DataFrame(
        {
            "longitude": [-100, -105, -98.4],
            "latitude": [40, 29, 42.3],
            "stid": ["aa", "bb", "cc"],
        }
    )

    x1 = ds.herbie.pick_points(points, method="nearest")
    xw = ds.herbie.pick_points(points, method="weighted")
    x4 = ds.herbie.pick_points(points, method="nearest", k=4)
    x8 = ds.herbie.pick_points(points, method="weighted", k=8)


def test_pick_points_simple():
    """Test a very simple grid."""
    ds = xr.Dataset(
        {"a": (["latitude", "longitude"], [[1, 0], [0, 0]])},
        coords={
            "latitude": (["latitude"], [45, 46]),
            "longitude": (["longitude"], [100, 101]),
        },
    )
    point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]})

    p = ds.herbie.pick_points(point, method="nearest", k=1)
    assert all(
        [
            p.latitude.item() == 45,
            p.longitude.item() == 100,
            p.point_grid_distance.round(2).item() == 34.02,
            p.point_latitude.item() == 45.25,
            p.point_longitude.item() == 100.25,
            p.a.item() == 1,
        ]
    )


def test_pick_points_nans_in_grid():
    """Tests when there are null values in the xarray dataset."""
    ds = xr.Dataset(
        {
            "a": (
                ["latitude", "longitude"],
                [[1, 0, np.nan], [0, 0, np.nan], [0, 1, np.nan]],
            )
        },
        coords={
            "latitude": (["latitude"], [45, 46, 47]),
            "longitude": (["longitude"], [100, 101, 102]),
        },
    )
    point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]})

    p = ds.herbie.pick_points(point, method="nearest", k=1)
    assert all(
        [
            p.latitude.item() == 45,
            p.longitude.item() == 100,
            p.point_grid_distance.round(2).item() == 34.02,
            p.point_latitude.item() == 45.25,
            p.point_longitude.item() == 100.25,
            p.a.item() == 1,
        ]
    )


def test_pick_points_pd_index_off():
    """Test a very simple grid."""
    ds = xr.Dataset(
        {"a": (["latitude", "longitude"], [[1, 0], [0, 0]])},
        coords={
            "latitude": (["latitude"], [45, 46]),
            "longitude": (["longitude"], [100, 101]),
        },
    )
    point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]}, index=[200])

    p = ds.herbie.pick_points(point, method="nearest", k=1)
    assert all(
        [
            p.latitude.item() == 45,
            p.longitude.item() == 100,
            p.point_grid_distance.round(2).item() == 34.02,
            p.point_latitude.item() == 45.25,
            p.point_longitude.item() == 100.25,
            p.a.item() == 1,
        ]
    )


def test_pick_points_self_points():
    """Test pick points with model's own grid points."""
    H = Herbie("2024-03-01", model="hrrr")
    ds = H.xarray(":TMP:2 m")

    n = 100
    points_self = (
        ds[["latitude", "longitude"]]
        .to_dataframe()[["latitude", "longitude"]]
        .sample(n)
        .reset_index(drop=True)
    )
    points_self["stid"] = [generate_random_string() for _ in range(n)]

    r1 = ds.herbie.pick_points(points_self)
    assert all(r1.point_grid_distance == 0)

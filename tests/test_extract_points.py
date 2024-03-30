"""Test the ds.herbie.extrac_points() accessor."""

import pandas as pd

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
        x4 = ds.herbie.extract_points(points, method=4)
        x8 = ds.herbie.extract_points(points, method=8)


def test_simple_test():
    """Test extract points with model's own grid points."""
    pass


def test_with_model_own_grid_method_nearest():
    """Test extract points with model's own grid points."""
    pass


def test_with_model_own_grid_method_weighted():
    """Test extract points with model's own grid points."""
    pass


def test_with_model_own_grid_method_xarray():
    """Test extract points with model's own grid points."""
    pass


def test_caching_tree():
    """Test the BallTree caching works as expected."""
    pass

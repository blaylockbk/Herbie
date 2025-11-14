"""This is the legacy nearest_points function.

It was replaced by pick_points.
"""

import warnings

import numpy as np
import pandas as pd


def nearest_points(ds, points, names=None, verbose=True):
    """
    Get the nearest latitude/longitude points from a xarray Dataset.

    - Stack Overflow: https://stackoverflow.com/questions/58758480/xarray-select-nearest-lat-lon-with-multi-dimension-coordinates
    - MetPy Details: https://unidata.github.io/MetPy/latest/tutorials/xarray_tutorial.html?highlight=assign_y_x

    Parameters
    ----------
    ds : xr.Dataset
        A Herbie-friendly xarray Dataset

    points : tuple, list of tuples, pd.DataFrame
        Points to be plucked from the gridded Dataset.
        There are multiple objects accepted.

        1. Tuple of longitude and latitude (lon, lat) coordinate pair.
        1. List of multiple (lon, lat) coordinate pair tuples.
        1. Pandas DataFrame with ``longitude`` and ``latitude`` columns. Index will be used as point names, unless ``names`` is specified.
        1. Shapeley Point or Points

    names : list
        A list of names for each point location (i.e., station name).
        None will not append any names. names should be the same
        length as points.

    Notes
    -----
        This is **much** faster than my old "pluck_points" method.
        For matching 1,948 points:
        - `nearest_points` completed in 7.5 seconds.
        - `pluck_points` completed in 2 minutes.

        TODO: Explore alternatives
        - Could Shapely nearest_points be used
        https://shapely.readthedocs.io/en/latest/manual.html#nearest-points
        - Or possibly scipy BallTree method.

    """
    try:
        import cartopy.crs as ccrs
        import shapely
        from shapely.geometry import MultiPoint, Point
    except ModuleNotFoundError:
        raise ModuleNotFoundError(
            "cartopy is an 'extra' requirements, please use "
            "`pip install 'herbie-data[extras]'` for the full functionality."
        )

    warnings.warn(
        "The accessor `ds.herbie.nearest_points` is deprecated in "
        "favor of the `ds.herbie.pick_points` which uses the "
        "BallTree algorithm instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # ds = self._obj

    # Longitude and Latitude point DataFrame
    if isinstance(points, pd.DataFrame):
        point_df = points[["longitude", "latitude"]]
        if names is not None:
            point_df.index = names
    elif np.shape(points) == (2,):
        # points is a tuple (lon, lat) or list [lon, lat]
        # and name is given as None or str
        point_df = pd.DataFrame(
            [points],
            columns=["longitude", "latitude"],
            index=[names],
        )
    elif isinstance(points, list):
        # points given as a list of coordinate-pair tuples
        # and name is given as a list of str
        point_df = pd.DataFrame(
            points,
            columns=["longitude", "latitude"],
            index=names,
        )
    elif isinstance(points, (MultiPoint, Point)):
        # points is given as a Shapely object
        point_df = pd.DataFrame(
            shapely.get_coordinates(points),
            columns=["longitude", "latitude"],
            index=names,
        )
    else:
        raise ValueError("The points supplied was not understood.")

    # Check if MetPy has already parsed the CF metadata grid projection.
    # Do that if it hasn't been done yet.
    if "metpy_crs" not in ds:
        ds = ds.metpy.parse_cf()

    # Apply the MetPy method `assign_y_x` to the dataset
    # https://unidata.github.io/MetPy/latest/api/generated/metpy.xarray.html?highlight=assign_y_x#metpy.xarray.MetPyDataArrayAccessor.assign_y_x
    ds = ds.metpy.assign_y_x()

    # Convert the requested [(lon,lat), (lon,lat)] points to map projection.
    # Accept a list of point tuples, or Shapely Points object.
    # We want to index the dataset at a single point.
    # We can do this by transforming a lat/lon point to the grid location
    crs = ds.metpy_crs.item().to_cartopy()

    transformed_data = crs.transform_points(
        ccrs.PlateCarree(), point_df.longitude, point_df.latitude
    )

    a = pd.DataFrame({"x": transformed_data[:, 0], "y": transformed_data[:, 1]})
    a.index.name = "point"

    # Select the nearest points from the projection coordinates.
    # Get corresponding values from xarray
    # https://docs.xarray.dev/en/stable/user-guide/indexing.html#more-advanced-indexing
    #
    new_ds = ds.sel(
        x=a["x"].to_xarray(),
        y=a["y"].to_xarray(),
        method="nearest",
    )

    new_ds.coords["point"] = ("point", point_df.index.to_list())
    new_ds.coords["point_latitude"] = ("point", point_df.latitude)
    new_ds.coords["point_longitude"] = ("point", point_df.longitude)

    return new_ds

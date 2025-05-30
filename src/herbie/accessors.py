## Brian Blaylock
## April 23, 2021

"""Herbie's xarray accessors.

Other useful packages

- salem: mask data by a geographic region: https://github.com/fmaussion/salem
- xoak: xarray nearest neighbor https://github.com/xarray-contrib/xoak
"""

import functools
import pickle
import re
import warnings
from pathlib import Path
from typing import Literal, Optional, Union

import numpy as np
import pandas as pd
import xarray as xr
from pyproj import CRS

import herbie

_level_units = dict(
    adiabaticCondensation="adiabatic condensation",
    atmosphere="atmosphere",
    atmosphereSingleLayer="atmosphere single layer",
    boundaryLayerCloudLayer="boundary layer cloud layer",
    cloudBase="cloud base",
    cloudCeiling="cloud ceiling",
    cloudTop="cloud top",
    depthBelowLand="m",
    equilibrium="equilibrium",
    heightAboveGround="m",
    heightAboveGroundLayer="m",
    highCloudLayer="high cloud layer",
    highestTroposphericFreezing="highest tropospheric freezing",
    isobaricInhPa="hPa",
    isobaricLayer="hPa",
    isothermZero="0 C",
    isothermal="K",
    level="m",
    lowCloudLayer="low cloud layer",
    meanSea="MSLP",
    middleCloudLayer="middle cloud layer",
    nominalTop="nominal top",
    pressureFromGroundLayer="Pa",
    sigma="sigma",
    sigmaLayer="sigmaLayer",
    surface="surface",
)


def add_proj_info(ds: xr.Dataset):
    """Add projection info to a Dataset."""
    raise NotImplementedError("This function `add_proj_info` is not yet implemented.")

    # TODO: remove pyproj dependency

    match = re.search(r'"source": "(.*?)"', ds.history)
    FILE = Path(match.group(1))

    # Get CF grid projection information with pygrib and pyproj because
    # this is something cfgrib doesn't do (https://github.com/ecmwf/cfgrib/issues/251)
    # NOTE: Assumes the projection is the same for all variables
    with pygrib.open(str(FILE)) as grb:
        msg = grb.message(1)
        cf_params = CRS(msg.projparams).to_cf()

    # Funny stuff with polar stereographic (https://github.com/pyproj4/pyproj/issues/856)
    # TODO: Is there a better way to handle this? What about south pole?
    if cf_params["grid_mapping_name"] == "polar_stereographic":
        cf_params["latitude_of_projection_origin"] = cf_params.get(
            "latitude_of_projection_origin", 90
        )

    # ----------------------
    # Attach CF grid mapping
    # ----------------------
    # http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#appendix-grid-mappings
    ds["gribfile_projection"] = None
    ds["gribfile_projection"].attrs = cf_params
    ds["gribfile_projection"].attrs["long_name"] = "model grid projection"

    # Assign this grid_mapping for all variables
    for var in list(ds):
        if var == "gribfile_projection":
            continue
        ds[var].attrs["grid_mapping"] = "gribfile_projection"


@xr.register_dataset_accessor("herbie")
class HerbieAccessor:
    """Accessor for xarray Datasets opened with Herbie."""

    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._center = None

    @property
    def center(self) -> tuple[float, float]:
        """Return the geographic center point of this dataset."""
        if self._center is None:
            # we can use a cache on our accessor objects, because accessors
            # themselves are cached on instances that access them.
            lon = self._obj.latitude
            lat = self._obj.longitude
            self._center = (float(lon.mean()), float(lat.mean()))
        return self._center

    def to_180(self) -> xr.Dataset:
        """Wrap longitude coordinates as range [-180,180]."""
        ds = self._obj
        ds["longitude"] = (ds["longitude"] + 180) % 360 - 180
        return ds

    def to_360(self) -> xr.Dataset:
        """Wrap longitude coordinates as range [0,360]."""
        ds = self._obj
        ds["longitude"] = (ds["longitude"] - 360) % 360
        return ds

    @functools.cached_property
    def crs(self):
        """
        Cartopy coordinate reference system (crs) from a cfgrib Dataset.

        Projection information is from the grib2 message for each variable.

        Parameters
        ----------
        ds : xarray.Dataset
            An xarray.Dataset from a GRIB2 file opened by the cfgrib engine.

        """
        try:
            import metpy
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "metpy is an 'extra' requirement, please use "
                "`pip install 'herbie-data[extras]'` for the full functionality."
            )

        ds = self._obj

        # Get variables that have dimensions
        # (this filters out the gribfile_projection variable)
        variables = [i for i in list(ds) if len(ds[i].dims) > 0]

        ds = ds.metpy.parse_cf(varname=variables)
        crs = ds.metpy_crs.item().to_cartopy()
        return crs

    @functools.cached_property
    def polygon(self):
        """Get a polygon of the domain boundary."""
        try:
            import cartopy.crs as ccrs
            from shapely.geometry import Polygon
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "cartopy is an 'extra' requirements, please use "
                "`pip install 'herbie-data[extras]'` for the full functionality."
            )

        ds = self._obj

        LON = ds.longitude.data
        LAT = ds.latitude.data

        # Path of array outside border starting from the lower left corner
        # and going around the array counter-clockwise.
        outside = (
            list(zip(LON[0, :], LAT[0, :]))
            + list(zip(LON[:, -1], LAT[:, -1]))
            + list(zip(LON[-1, ::-1], LAT[-1, ::-1]))
            + list(zip(LON[::-1, 0], LAT[::-1, 0]))
        )
        outside = np.array(outside)

        ###############################
        # Polygon in Lat/Lon coordinates
        x = outside[:, 0]
        y = outside[:, 1]
        domain_polygon_latlon = Polygon(zip(x, y))

        ###################################
        # Polygon in projection coordinates
        transform = self.crs.transform_points(ccrs.PlateCarree(), x, y)

        # Remove any points that run off the projection map (i.e., point's value is `inf`).
        transform = transform[~np.isinf(transform).any(axis=1)]
        x = transform[:, 0]
        y = transform[:, 1]
        domain_polygon = Polygon(zip(x, y))

        return domain_polygon, domain_polygon_latlon

    def with_wind(
        self, which: Literal["both", "speed", "direction"] = "both"
    ) -> xr.Dataset:
        """Return Dataset with calculated wind speed and/or direction.

        Consistent with the eccodes GRIB parameter database, variables
        names are assigned as follows:

        - "si10"   : 10 metre wind speed (note this is not ws10 as you might expect)
        - "wdir10" : 10 metre wind direction
        - "ws"     : wind speed
        - "wdir"   : wind direction

        Refer to the eccodes database <https://codes.ecmwf.int/grib/param-db/>.

        Parameters
        ----------
        which : {'both', 'speed', 'direction'}
            Specify which wind quantity to compute.

        """
        ds = self._obj

        n_computed = 0

        if which in ("speed", "both"):
            if {"u10", "v10"}.issubset(ds):
                ds["si10"] = np.sqrt(ds.u10**2 + ds.v10**2)
                ds["si10"].attrs["GRIB_paramId"] = 207
                ds["si10"].attrs["long_name"] = "10 metre wind speed"
                ds["si10"].attrs["units"] = "m s**-1"
                ds["si10"].attrs["standard_name"] = "wind_speed"
                ds["si10"].attrs["grid_mapping"] = ds.u10.attrs.get("grid_mapping")
                n_computed += 1

            if {"u100", "v100"}.issubset(ds):
                ds["si100"] = np.sqrt(ds.u100**2 + ds.v100**2)
                ds["si100"].attrs["GRIB_paramId"] = 228249
                ds["si100"].attrs["long_name"] = "100 metre wind speed"
                ds["si100"].attrs["units"] = "m s**-1"
                ds["si100"].attrs["standard_name"] = "wind_speed"
                ds["si100"].attrs["grid_mapping"] = ds.u100.attrs.get("grid_mapping")
                n_computed += 1

            if {"u80", "v80"}.issubset(ds):
                ds["si80"] = np.sqrt(ds.u80**2 + ds.v80**2)
                ds["si80"].attrs["long_name"] = "80 metre wind speed"
                ds["si80"].attrs["units"] = "m s**-1"
                ds["si80"].attrs["standard_name"] = "wind_speed"
                ds["si80"].attrs["grid_mapping"] = ds.u80.attrs.get("grid_mapping")
                n_computed += 1

            if {"u", "v"}.issubset(ds):
                ds["ws"] = np.sqrt(ds.u**2 + ds.v**2)
                ds["ws"].attrs["GRIB_paramId"] = 10
                ds["ws"].attrs["long_name"] = "wind speed"
                ds["ws"].attrs["units"] = "m s**-1"
                ds["ws"].attrs["standard_name"] = "wind_speed"
                ds["ws"].attrs["grid_mapping"] = ds.u.attrs.get("grid_mapping")
                n_computed += 1

        if which in ("direction", "both"):
            if {"u10", "v10"}.issubset(ds):
                ds["wdir10"] = (
                    (270 - np.rad2deg(np.arctan2(ds.v10, ds.u10))) % 360
                ).where((ds.u10 != 0) | (ds.v10 != 0))
                ds["wdir10"].attrs["GRIB_paramId"] = 260260
                ds["wdir10"].attrs["long_name"] = "10 metre wind direction"
                ds["wdir10"].attrs["units"] = "degree"
                ds["wdir10"].attrs["standard_name"] = "wind_from_direction"
                ds["wdir10"].attrs["grid_mapping"] = ds.u10.attrs.get("grid_mapping")
                n_computed += 1

            if {"u100", "v100"}.issubset(ds):
                ds["wdir100"] = (
                    (270 - np.rad2deg(np.arctan2(ds.v100, ds.u100))) % 360
                ).where((ds.u100 != 0) | (ds.v100 != 0))
                ds["wdir100"].attrs["long_name"] = "100 metre wind direction"
                ds["wdir100"].attrs["units"] = "degree"
                ds["wdir100"].attrs["standard_name"] = "wind_from_direction"
                ds["wdir100"].attrs["grid_mapping"] = ds.u100.attrs.get("grid_mapping")
                n_computed += 1

            if {"u80", "v80"}.issubset(ds):
                ds["wdir80"] = (
                    (270 - np.rad2deg(np.arctan2(ds.v80, ds.u80))) % 360
                ).where((ds.u80 != 0) | (ds.v80 != 0))
                ds["wdir80"].attrs["long_name"] = "80 metre wind direction"
                ds["wdir80"].attrs["units"] = "degree"
                ds["wdir80"].attrs["standard_name"] = "wind_from_direction"
                ds["wdir80"].attrs["grid_mapping"] = ds.u80.attrs.get("grid_mapping")
                n_computed += 1

            if {"u", "v"}.issubset(ds):
                ds["wdir"] = ((270 - np.rad2deg(np.arctan2(ds.v, ds.u))) % 360).where(
                    (ds.u != 0) | (ds.v != 0)
                )
                ds["wdir"].attrs["GRIB_paramId"] = 3031
                ds["wdir"].attrs["long_name"] = "wind direction"
                ds["wdir"].attrs["units"] = "degree"
                ds["wdir"].attrs["standard_name"] = "wind_from_direction"
                ds["wdir"].attrs["grid_mapping"] = ds.u.attrs.get("grid_mapping")
                n_computed += 1

        if n_computed == 0:
            warnings.warn("`with_wind()` did not do anything.")

        return ds

    def pick_points(
        self,
        points: pd.DataFrame,
        method: Literal["nearest", "weighted"] = "nearest",
        *,
        k: Optional[int] = None,
        max_distance: Union[int, float] = 500,
        use_cached_tree: Union[bool, Literal["replant"]] = True,
        tree_name: Optional[str] = None,
        verbose: bool = False,
    ) -> xr.Dataset:
        """Pick nearest neighbor grid values at selected  points.

        Parameters
        ----------
        points : Pandas DataFrame
            A DataFrame with columns 'latitude' and 'longitude'
            representing the points to match to the model grid.
        method : {'nearest', 'weighted'}
            Method used to pick points.
            - `nearest` : Gets grid value nearest the requested point.
            - `weighted`: Gets four grid value nearest the requested
                point and compute the inverse-distance-weighted mean.
        k : None or int
            If None and method is nearest, `k=1`.
            If None and method is weighted, `k=4`.
            Else, specify the number of neighbors to find.
        max_distance : int or float
            Maximum distance in kilometers allowed for nearest neighbor
            search. Default is 500 km, which is very generous for any
            model grid. This can help the case when a requested point
            is off the grid.
        use_cached_tree : {True, False, "replant"}
            Controls if the BallTree object is caches for later use.
            By "plant", I mean, "create a new BallTree object."
            - `True` : Plant+save BallTree if it doesn't exist; load
                saved BallTree if one exists.
            - `False`: Plant the BallTree, even if one exists.
            - `"replant"` : Plant a new BallTree and save a new pickle.
        tree_name : str
            If None, use the ds.model and domain size as the tree's name.
            If ds.model does not exists, then the BallTree will not be
            cached, unless you provide the tree_name.

        Examples
        --------
        >>> H = Herbie("2024-03-28 00:00", model="hrrr")
        >>> ds = H.xarray("TMP:[5,6,7,8,9][0,5]0 mb", remove_grib=False)
        >>> points = pd.DataFrame(
        ...     {
        ...         "longitude": [-100, -105, -98.4],
        ...         "latitude": [40, 29, 42.3],
        ...         "stid": ["aa", "bb", "cc"],
        ...     }
        ... )

        Pick value at the nearest neighbor point
        >>> dsp = ds.herbie.pick_points(points, method="nearest")

        Get the weighted mean of the four nearest neighbor points
        >>> dsp = ds.herbie.pick_points(points, method="weighted")

        A Dataset is returned of the original grid reduced to the
        requested points, with the values from the `points` dataset
        added as new coordinates.

        A user can easily convert the result to a Pandas DataFrame
        >>> dsp.to_dataframe()

        If you want to select points by a station name, swap the
        dimension.
        >>> dsp = dsp.swap_dims({"point": "point_stid"})
        """
        try:
            from sklearn.neighbors import BallTree
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "scikit-learn is an 'extra' requirement, please use "
                "`pip install 'herbie-data[extras]'` for the full functionality."
            )

        def plant_tree(save_pickle: Optional[Union[Path, str]] = None):
            """Grow a new BallTree object from seedling."""
            timer = pd.Timestamp("now")
            print("INFO: 🌱 Growing new BallTree...", end="")
            tree = BallTree(np.deg2rad(df_grid), metric="haversine")
            print(
                f"🌳 BallTree grew in {(pd.Timestamp('now') - timer).total_seconds():.2} seconds."
            )
            if save_pickle:
                try:
                    Path(save_pickle).parent.mkdir(parents=True, exist_ok=True)
                    with open(save_pickle, "wb") as f:
                        pickle.dump(tree, f)
                    print(f"INFO: Saved BallTree to {save_pickle}")
                except OSError:
                    print(f"ERROR: Could not save BallTree to {save_pickle}.")
            return tree

        ds = self._obj

        # ---------------------
        # Validate points input
        if ("latitude" not in points) and ("longitude" not in points):
            raise ValueError(
                "`points` DataFrame must have columns 'latitude' and 'longitude'"
            )

        if not all(points.latitude.between(-90, 90, inclusive="both")):
            raise ValueError("All latitude points must be [-90,90]")

        if not all(points.longitude.between(0, 360, inclusive="both")):
            if not all(points.longitude.between(-180, 180, inclusive="both")):
                raise ValueError("All longitude points must be [-180,180] or [0,360]")

        # ---------------------
        # Validate method input
        _method = set(["nearest", "weighted"])

        if method == "nearest" and k is None:
            # Get the value at the nearest grid point using BallTree
            k = 1
        elif method == "weighted" and k is None:
            # Compute the value of each variable from the inverse-
            # weighted distance of the values of the four nearest
            # neighbors.
            k = 4
        elif method in _method and isinstance(k, int):
            # Get the k nearest neighbors and return the values (nearest)
            # or compute the distance-weighted mean (weighted).
            pass
        else:
            raise ValueError(
                f"`method` must be one of {_method} and `k` must be an int or None."
            )

        # Only consider variables that have dimensions.
        ds = ds[[i for i in ds if ds[i].dims != ()]]

        if "latitude" in ds.dims and "longitude" in ds.dims:
            # Rename dims to x and y
            # This is needed for regular latitude-longitude grids like
            # GFS and IFS model data.
            ds = ds.rename_dims({"latitude": "y", "longitude": "x"})

        # Get Dataset's lat/lon grid and coordinate indices as a DataFrame.
        df_grid = (
            ds[["latitude", "longitude"]]
            .drop_vars([i for i, j in ds.coords.items() if not j.ndim])
            .to_dataframe()
        )

        # ---------------
        # BallTree object
        # Plant, plant+Save, or load

        if tree_name is None:
            tree_name = getattr(ds, "model", "UNKNOWN")

        if use_cached_tree and tree_name == "UNKNOWN":
            use_cached_tree = False
            print(
                "WARNING: Herbie won't cache the BallTree because it\n"
                "         doesn't know what to name it. Please specify\n"
                "         `tree_name` to cache the tree for use later."
            )

        pkl_BallTree_file = (
            herbie.config["default"]["save_dir"]
            / "BallTree"
            / f"{tree_name}_{ds.x.size}-{ds.y.size}.pkl"
        )

        if not use_cached_tree:
            # Create a new BallTree. Do not save pickle.
            tree = plant_tree(save_pickle=False)
        elif use_cached_tree == "replant" or not pkl_BallTree_file.exists():
            # Create a new BallTree and save pickle.
            tree = plant_tree(save_pickle=pkl_BallTree_file)
        elif use_cached_tree:
            # Load BallTree from pickle.
            with open(pkl_BallTree_file, "rb") as f:
                tree = pickle.load(f)

        # -------------------------------------
        # Query points to find nearest neighbor
        # Note: Order matters, and lat/long must be in radians.
        # TODO: Maybe add option to use MultiProcessing here, to split
        # TODO:   the Dataset into chunks; or maybe not needed because
        # TODO:   the method is fast enough without the added complexity.
        dist, ind = tree.query(np.deg2rad(points[["latitude", "longitude"]]), k=k)

        # Convert distance to km by multiplying by the radius of the Earth
        dist *= 6371

        # Pick grid values for each value of k
        k_points = []
        df_grid = df_grid.reset_index()
        for i in range(k):
            a = points.copy()
            a["point_grid_distance"] = dist[:, i]
            a["grid_index"] = ind[:, i]

            a = pd.concat(
                [
                    a.reset_index(drop=True),
                    df_grid.iloc[a.grid_index]
                    .add_suffix("_grid")
                    .reset_index(drop=True),
                ],
                axis=1,
            )
            a.index.name = "point"

            if max_distance:
                flagged = a.loc[a.point_grid_distance > max_distance]
                a = a.loc[a.point_grid_distance <= max_distance]
                if len(flagged):
                    print(
                        f"WARNING: {len(flagged)} points removed for exceeding {max_distance=} km threshold."
                    )
                    print(f"{flagged}")
                    print("")

            # Get corresponding values from xarray
            # https://docs.xarray.dev/en/stable/user-guide/indexing.html#more-advanced-indexing
            ds_points = ds.sel(
                x=a.x_grid.to_xarray().dropna("point").astype("int"),
                y=a.y_grid.to_xarray().dropna("point").astype("int"),
            )
            ds_points.coords["point_grid_distance"] = a.point_grid_distance.to_xarray()
            ds_points["point_grid_distance"].attrs["long_name"] = (
                "Distance between requested point and nearest grid point."
            )
            ds_points["point_grid_distance"].attrs["units"] = "km"

            for i in points.columns:
                ds_points.coords[f"point_{i}"] = a[i].to_xarray()
                ds_points[f"point_{i}"].attrs["long_name"] = f"Requested grid point {i}"

            k_points.append(ds_points.drop_vars("point"))

        if method == "nearest" and k == 1:
            return k_points[0]

        elif method == "nearest" and k > 1:
            # New dimension k is the index of the n-th nearest neighbor
            return xr.concat(k_points, dim="k")

        elif method == "weighted":
            # Compute the inverse-distance weighted mean for each
            # variable from the four nearest points.
            b = xr.concat(k_points, dim="k")

            # Note: clipping accounts for the "divide by zero" case when
            # the requested point is exactly the nearest grid point.
            weights = (1 / b.point_grid_distance).clip(max=1e6)

            # Compute weighted mean of variables
            sum_of_weights = weights.sum(dim="k")
            weighted_sum = (b * weights).sum(dim="k")

            c = weighted_sum / sum_of_weights

            # Include some coordinates that were dropped as a result of
            # the line `weights.sum(dim='k')`.
            c.coords["latitude"] = b.coords["latitude"]
            c.coords["longitude"] = b.coords["longitude"]
            c.coords["point_grid_distance"] = b.coords["point_grid_distance"]

            return c
        else:
            raise ValueError("I didn't expect to be here.")

    def nearest_points(self, points, names=None, verbose=True):
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

        ds = self._obj

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

    def plot(self, ax=None, common_features_kw={}, vars=None, **kwargs):
        """Plot data on a map.

        TODO: Work in progress!

        Parameters
        ----------
        vars : list
            List of variables to plot. Default None will plot all
            variables in the DataSet.
        """
        raise NotImplementedError("Plotting functionality is not working right now.")

        try:
            import matplotlib.pyplot as plt

            from herbie import paint
            from herbie.toolbox import EasyMap, pc
        except ModuleNotFoundError:
            raise ModuleNotFoundError(
                "cartopy is an 'extra' requirement. Please use "
                "`pip install 'herbie-data[extras]'` for the full functionality."
            )

        ds = self._obj

        if isinstance(vars, str):
            vars = [vars]

        if vars is None:
            vars = ds.data_vars

        for i, var in enumerate(vars):
            if "longitude" not in ds[var].coords:
                # This is the case for the gribfile_projection variable
                continue

            print("cfgrib variable:", var)
            print("GRIB_cfName", ds[var].attrs.get("GRIB_cfName"))
            print("GRIB_cfVarName", ds[var].attrs.get("GRIB_cfVarName"))
            print("GRIB_name", ds[var].attrs.get("GRIB_name"))
            print("GRIB_units", ds[var].attrs.get("GRIB_units"))
            print("GRIB_typeOfLevel", ds[var].attrs.get("GRIB_typeOfLevel"))
            print()

            ds[var].attrs["units"] = (
                ds[var]
                .attrs["units"]
                .replace("**-1", "$^{-1}$")
                .replace("**-2", "$^{-2}$")
            )

            defaults = dict(
                scale="50m",
                dpi=150,
                figsize=(10, 5),
                crs=ds.herbie.crs,
                ax=ax,
            )

            common_features_kw = {**defaults, **common_features_kw}

            ax = EasyMap(fignum=i, **common_features_kw).STATES().ax

            title = ""
            kwargs.setdefault("shading", "auto")
            cbar_kwargs = dict(pad=0.01)

            if ds[var].GRIB_cfVarName in ["d2m", "dpt"]:
                ds[var].attrs["GRIB_cfName"] = "dew_point_temperature"

            ## Wind
            wind_pair = {"u10": "v10", "u80": "v80", "u": "v"}

            if ds[var].GRIB_cfName == "air_temperature":
                kwargs = {**paint.NWSTemperature.kwargs2, **kwargs}
                cbar_kwargs = {**paint.NWSTemperature.cbar_kwargs2, **cbar_kwargs}
                if ds[var].GRIB_units == "K":
                    ds[var] -= 273.15
                    ds[var].attrs["GRIB_units"] = "C"
                    ds[var].attrs["units"] = "C"

            elif ds[var].GRIB_cfName == "dew_point_temperature":
                kwargs = {**paint.NWSDewPointTemperature.kwargs2, **kwargs}
                cbar_kwargs = {
                    **paint.NWSDewPointTemperature.cbar_kwargs2,
                    **cbar_kwargs,
                }
                if ds[var].GRIB_units == "K":
                    ds[var] -= 273.15
                    ds[var].attrs["GRIB_units"] = "C"
                    ds[var].attrs["units"] = "C"

            elif ds[var].GRIB_name == "Total Precipitation":
                title = "-".join(
                    [f"F{int(i):02d}" for i in ds[var].GRIB_stepRange.split("-")]
                )
                ds[var] = ds[var].where(ds[var] != 0)
                kwargs = {**paint.NWSPrecipitation.kwargs2, **kwargs}
                cbar_kwargs = {**paint.NWSPrecipitation.cbar_kwargs2, **cbar_kwargs}

            elif ds[var].GRIB_name == "Maximum/Composite radar reflectivity":
                ds[var] = ds[var].where(ds[var] >= 0)
                kwargs = {**paint.RadarReflectivity.kwargs2, **kwargs}
                cbar_kwargs = {**paint.RadarReflectivity.cbar_kwargs2, **cbar_kwargs}

            elif ds[var].GRIB_cfName == "relative_humidity":
                kwargs = {**paint.NWSRelativeHumidity.kwargs2, **kwargs}
                cbar_kwargs = {**paint.NWSRelativeHumidity.cbar_kwargs2, **cbar_kwargs}

            elif ds[var].GRIB_name == "Orography":
                if "lsm" in ds:
                    ds["orog"] = ds.orog.where(ds.lsm == 1, -100)

                kwargs = {**paint.LandGreen.kwargs, **kwargs}
                # cbar_kwargs = {**cm_terrain().cbar_kwargs, **cbar_kwargs}

            elif "wind" in ds[var].GRIB_cfName or "wind" in ds[var].GRIB_name:
                cbar_kwargs = {**cm_wind().cbar_kwargs, **cbar_kwargs}
                kwargs = {**cm_wind().cmap_kwargs, **kwargs}
                if ds[var].GRIB_cfName == "eastward_wind":
                    cbar_kwargs["label"] = "U " + cbar_kwargs["label"]
                elif ds[var].GRIB_cfName == "northward_wind":
                    cbar_kwargs["label"] = "V " + cbar_kwargs["label"]
            else:
                cbar_kwargs = {
                    **dict(
                        label=f"{ds[var].GRIB_parameterName.strip().title()} ({ds[var].units})"
                    ),
                    **cbar_kwargs,
                }

            p = ax.pcolormesh(
                ds.longitude, ds.latitude, ds[var], transform=pc, **kwargs
            )
            plt.colorbar(p, ax=ax, **cbar_kwargs)

            VALID = pd.to_datetime(ds.valid_time.data).strftime("%H:%M UTC %d %b %Y")
            RUN = pd.to_datetime(ds.time.data).strftime("%H:%M UTC %d %b %Y")
            FXX = f"F{pd.to_timedelta(ds.step.data).total_seconds() / 3600:02.0f}"

            level_type = ds[var].GRIB_typeOfLevel
            if level_type in _level_units:
                level_units = _level_units[level_type]
            else:
                level_units = "unknown"

            if level_units.lower() in ["surface", "atmosphere"]:
                level = f"{title} {level_units}"
            else:
                level = f"{ds[var][level_type].data:g} {level_units}"

            ax.set_title(
                f"Run: {RUN} {FXX}",
                loc="left",
                fontfamily="monospace",
                fontsize="x-small",
            )
            ax.set_title(
                f"{ds.model.upper()} {level}\n", loc="center", fontweight="semibold"
            )
            ax.set_title(
                f"Valid: {VALID}",
                loc="right",
                fontfamily="monospace",
                fontsize="x-small",
            )

            # Set extent so no whitespace shows around pcolormesh area
            # TODO: Any better way to do this? With metpy.assign_y_x
            # !!!!: The `metpy.assign_y_x` method could be used for pluck_point :)
            try:
                if "x" in ds.dims:
                    ds = ds.metpy.parse_cf()
                    ds = ds.metpy.assign_y_x()

                    ax.set_extent(
                        [
                            ds.x.min().item(),
                            ds.x.max().item(),
                            ds.y.min().item(),
                            ds.y.max().item(),
                        ],
                        crs=ds.herbie.crs,
                    )
            except Exception:
                pass

        return ax

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
from .pick_points import GridPointPicker

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
            lat = self._obj.latitude
            lon = self._obj.longitude
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
        """Pick nearest neighbor grid values at selected points.

        Parameters
        ----------
        points : pd.DataFrame
            DataFrame with 'latitude' and 'longitude' columns
        method : {'nearest', 'weighted'}
            Method for point picking:
            - 'nearest': Get value at nearest grid point
            - 'weighted': Inverse-distance weighted mean of k nearest points
        k : int, optional
            Number of nearest neighbors. Defaults to 1 for 'nearest',
            4 for 'weighted'
        max_distance : float
            Maximum distance in km for valid neighbors (default: 500)
        use_cached_tree : bool or 'replant'
            Whether to cache the BallTree spatial index:
            - True: Use cached tree if exists, create and cache if not
            - False: Always create new tree, don't cache
            - 'replant': Force create new tree and cache it
        tree_name : str, optional
            Custom name for BallTree cache file. If None, uses ds.model
        verbose : bool
            Print verbose output (currently unused)

        Returns
        -------
        xr.Dataset
            Dataset with values at requested points. Includes coordinates:
            - point_latitude, point_longitude: requested coordinates
            - point_grid_distance: distance to nearest grid point (km)
            - Any other columns from points DataFrame

        Examples
        --------
        >>> H = Herbie("2024-03-28 00:00", model="hrrr")
        >>> ds = H.xarray("TMP:[5,6,7,8,9][0,5]0 mb")
        >>> points = pd.DataFrame({
        ...     "longitude": [-100, -105, -98.4],
        ...     "latitude": [40, 29, 42.3],
        ...     "stid": ["aa", "bb", "cc"],
        ... })

        Get nearest neighbor values:
        >>> dsp = ds.herbie.pick_points(points, method="nearest")

        Get distance-weighted mean of 4 nearest points:
        >>> dsp = ds.herbie.pick_points(points, method="weighted")

        Convert to DataFrame:
        >>> df = dsp.to_dataframe()

        Index by station ID:
        >>> dsp = dsp.swap_dims({"point": "point_stid"})
        """
        cache_dir = herbie.config["default"]["save_dir"]

        picker = GridPointPicker(
            ds=self._obj,
            cache_dir=cache_dir,
            tree_name=tree_name,
        )

        return picker.pick_points(
            points=points,
            method=method,
            k=k,
            max_distance=max_distance,
            use_cached_tree=use_cached_tree,
        )

    def nearest_points(self, points, names=None, verbose=True):
        """Legacy point extractor."""
        from herbie.nearest_points import nearest_points

        return nearest_points(
            ds=self._obj,
            points=points,
            names=names,
            verbose=verbose,
        )

    def plot(self, ax=None, common_features_kw={}, vars=None, **kwargs):
        """Plot data on a map.

        Parameters
        ----------
        vars : list
            List of variables to plot. Default None will plot all
            variables in the DataSet.
        """
        raise NotImplementedError(
            "Plotting functionality is not working right now. If you have ideas, please open a PR."
        )

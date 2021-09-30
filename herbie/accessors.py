## Brian Blaylock
## April 23, 2021

"""
==================================
Herbie Extension: xarray accessors
==================================

Extend the xarray capabilities with a custom accessor.
http://xarray.pydata.org/en/stable/internals.html#extending-xarray

To use the herbie xarray accessor, do this...

.. code-block:: python

    H = Herbie('2021-01-01', model='hrrr')
    ds = H.xarray('TMP:2 m')
    ds.herbie.crs
    ds.herbie.plot

"""
import warnings

import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import metpy
import numpy as np
import pandas as pd
import xarray as xr
from paint.radar import cm_reflectivity
from paint.radar2 import cm_reflectivity
from paint.standard2 import cm_dpt, cm_pcp, cm_rh, cm_tmp, cm_wind

# From Carpenter_Workshop:
# https://github.com/blaylockbk/Carpenter_Workshop
# TODO: update to the new cartopy_tools
from toolbox.cartopy_tools import common_features, pc


@xr.register_dataset_accessor("herbie")
class HerbieAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._center = None

    @property
    def center(self):
        """Return the geographic center point of this dataset."""
        if self._center is None:
            # we can use a cache on our accessor objects, because accessors
            # themselves are cached on instances that access them.
            lon = self._obj.latitude
            lat = self._obj.longitude
            self._center = (float(lon.mean()), float(lat.mean()))
        return self._center

    @property
    def crs(self):
        """
        Cartopy coordinate reference system (crs) from a cfgrib Dataset.

        Projection information is from the grib2 message for each variable.

        Parameters
        ----------
        ds : xarray.Dataset
            An xarray.Dataset from a GRIB2 file opened by the cfgrib engine.
        """

        ds = self._obj
        ds = ds.metpy.parse_cf()
        crs = ds.metpy_crs.item().to_cartopy()
        return crs

    def plot(self, ax=None, common_features_kw={}, **kwargs):
        """Plot data on a map."""
        ds = self._obj

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

        for var in ds.data_vars:
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

            ax = common_features(**common_features_kw).STATES().ax

            title = ""
            kwargs = {}
            cbar_kwargs = dict(pad=0.01)

            if ds[var].GRIB_cfVarName in ["d2m", "dpt"]:
                ds[var].attrs["GRIB_cfName"] = "dew_point_temperature"

            ## Wind
            wind_pair = {"u10": "v10", "u80": "v80", "u": "v"}

            if ds[var].GRIB_cfName == "air_temperature":
                kwargs = {**cm_tmp().cmap_kwargs, **kwargs}
                cbar_kwargs = {**cm_tmp().cbar_kwargs, **cbar_kwargs}
                if ds[var].GRIB_units == "K":
                    ds[var] -= 273.15
                    ds[var].attrs["GRIB_units"] = "C"
                    ds[var].attrs["units"] = "C"

            elif ds[var].GRIB_cfName == "dew_point_temperature":
                kwargs = {**cm_dpt().cmap_kwargs, **kwargs}
                cbar_kwargs = {**cm_dpt().cbar_kwargs, **cbar_kwargs}
                if ds[var].GRIB_units == "K":
                    ds[var] -= 273.15
                    ds[var].attrs["GRIB_units"] = "C"
                    ds[var].attrs["units"] = "C"

            elif ds[var].GRIB_name == "Total Precipitation":
                title = "-".join(
                    [f"F{int(i):02d}" for i in ds[var].GRIB_stepRange.split("-")]
                )
                ds[var] = ds[var].where(ds[var] != 0)
                kwargs = {**cm_pcp().cmap_kwargs, **kwargs}
                cbar_kwargs = {**cm_pcp().cbar_kwargs, **cbar_kwargs}

            elif ds[var].GRIB_name == "Maximum/Composite radar reflectivity":
                ds[var] = ds[var].where(ds[var] >= 0)
                cbar_kwargs = {**cm_reflectivity().cbar_kwargs, **cbar_kwargs}
                kwargs = {**cm_reflectivity().cmap_kwargs, **kwargs}

            elif ds[var].GRIB_cfName == "relative_humidity":
                cbar_kwargs = {**cm_rh().cbar_kwargs, **cbar_kwargs}
                kwargs = {**cm_rh().cmap_kwargs, **kwargs}

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
            FXX = f"F{pd.to_timedelta(ds.step.data).total_seconds()/3600:02.0f}"

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
            except:
                pass

        return ax

## Brian Blaylock
## April 23, 2021

"""
==================================
HRRR-B Extension: xarray accessors
==================================

Extend the xarray capabilities with a custom accessor.
http://xarray.pydata.org/en/stable/internals.html#extending-xarray

"""
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from paint.radar import cm_reflectivity
from paint.radar2 import cm_reflectivity
from paint.standard2 import cm_dpt, cm_pcp, cm_rh, cm_tmp, cm_wind
from toolbox.cartopy_tools_OLD import common_features, pc


@xr.register_dataset_accessor("hrrrb")
class hrrrb_accessor:
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
            print("cfgrib variable:", var)
            print("GRIB_cfName", ds[var].GRIB_cfName)
            print("GRIB_cfVarName", ds[var].GRIB_cfVarName)
            print("GRIB_name", ds[var].GRIB_name)
            print("GRIB_units", ds[var].GRIB_units)
            print("GRIB_typeOfLevel", ds[var].GRIB_typeOfLevel)
            print()
            ds[var].attrs["units"] = (
                ds[var]
                .attrs["units"]
                .replace("**-1", "$^{-1}$")
                .replace("**-2", "$^{-2}$")
            )

            dpi = common_features_kw.pop("dpi", 150)
            figsize = common_features_kw.pop("figsize", [10, 5])
            fig, ax = plt.subplots(
                1, 1, subplot_kw=dict(projection=ds.crs), dpi=dpi, figsize=figsize
            )

            default = dict(scale="50m", ax=ax, crs=ds.crs, STATES=True, BORDERS=True)
            common_features_kw = {**default, **common_features_kw}
            common_features(**common_features_kw)

            title = ""
            kwargs = {}
            cbar_kwargs = dict(pad=0.01)

            if ds[var].GRIB_cfVarName in ["d2m", "dpt"]:
                ds[var].attrs["GRIB_cfName"] = "dew_point_temperature"

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
            ax.set_title(f"HRRR {level}", loc="center", fontweight="semibold")
            ax.set_title(
                f"Valid: {VALID}",
                loc="right",
                fontfamily="monospace",
                fontsize="x-small",
            )

            # Set extent (could do this more efficiently by storing the data elsewhere)
            new = ds.crs.transform_points(pc, ds.longitude.data, ds.latitude.data)
            LONS = new[:, :, 0]
            LATS = new[:, :, 1]
            ax.set_extent([LONS.min(), LONS.max(), LATS.min(), LATS.max()], crs=ds.crs)

        return ax

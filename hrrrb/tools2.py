## Brian Blaylock
## April 23, 2021

"""
==================================
HRRR-B Extension: xarray accessors
==================================

Extend the xarray capabilities with a custom accessor.
http://xarray.pydata.org/en/stable/internals.html#extending-xarray

"""

import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from toolbox.cartopy_tools import common_features, pc
from paint.standard2 import cm_tmp, cm_dpt, cm_rh, cm_wind

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

    def plot(self, ax=None, **kwargs):
        """Plot data on a map."""
        ds = self._obj

        for var in ds.data_vars:
            print(var)
            print(ds[var].GRIB_cfName)
            print(ds[var].GRIB_cfVarName)
            print(ds[var].GRIB_units)
            print()
            ds[var].attrs['units'] = ds[var].attrs['units'].replace('**-1', '$^{-1}$')
            
            fig, ax = plt.subplots(1,1, subplot_kw=dict(projection=ds.crs))
            common_features(ax=ax, crs=ds.crs, STATES=True)
            kwargs = {}
            if ds[var].GRIB_cfName == 'air_temperature':
                kwargs = {**cm_tmp().cmap_kwargs, **kwargs}
                if ds[var].GRIB_units == 'K':
                    ds[var] -= 273.15
                    ds[var].attrs['GRIB_units'] = 'C'
                    ds[var].attrs['units'] = 'C'
            elif ds[var].GRIB_cfVarName == 'd2m':
                kwargs = {**cm_dpt().cmap_kwargs, **kwargs}
                if ds[var].GRIB_units == 'K':
                    ds[var] -= 273.15
                    ds[var].attrs['GRIB_units'] = 'C'
                    ds[var].attrs['units'] = 'C'
            elif ds[var].GRIB_cfName == 'relative_humidity':
                kwargs = {**cm_rh().cmap_kwargs, **kwargs}
            else:
                kwargs = {}
            
            ds[var].plot(x='longitude', y='latitude', 
                        ax=ax, transform=pc, **kwargs)

        
        return "plotting!"
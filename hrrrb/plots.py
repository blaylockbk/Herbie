## Brian Blaylock
## September 28, 2020

"""
==========
HRRR Plots
==========
"""
import warnings

import cartopy.crs as ccrs
import cartopy.feature as feature
import cartopy.io.img_tiles as cimgt
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from shapely.geometry import Polygon

try:
    from metpy.plots import USCOUNTIES
except:
    print('metpy package not found/imported, so you can not plot US Counties')


def simple_plot(ds, ax=None):
    """
    Make a simple plot for each variable.
    """
    if isinstance(ds, list):
        # A little recursion, for the case when get_hrrr returns a list
        # of xr.Datasets...
        for i in ds:
            simple_plot(i, ax=ax)
        return None

    for var in ds.data_vars:
        fig = plt.figure()
        ax = plt.axes(projection=ds.crs)
        ds[var].plot(x='longitude', y='latitude',
                     ax=ax, transform=ccrs.PlateCarree())
        ax.coastlines()
    return None

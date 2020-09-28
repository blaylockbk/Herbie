## Brian Blaylock
## September 28, 2020

"""
==========
HRRR Plots
==========
"""

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

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


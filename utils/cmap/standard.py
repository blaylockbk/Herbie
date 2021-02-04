# Brian Blaylock
# May 2, 2018

"""
=========================
NWS Standard Color Curves
=========================

Standardized colormaps from National Weather Service

- Source: Joseph Moore <joseph.moore@noaa.gov>
- Document: ./NWS Standard Color Curve Summary.pdf

Returns dictionaries with kwargs used to assign a matplolib plots colormap
and the colorbar labels.

For example:

.. code-block:: python
    
    import matplotlib.pyplot as plt
    import numpy as np
    from hrrrb.utils.cmap.standard import cm_tmp
    
    cm_cmap, cm_colorbar = cm_tmp()
    
    plt.pcolormesh(np.random.rand(8,8)*35, **cm_cmap)
    cb = plt.colorbar(**cm_colorbar)

"""
import matplotlib as mpl
mpl.use('Agg') 

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import matplotlib as mpl

def cm_tmp(display_cmap=False, levels=40):
    """
    Colormap for temperature in Celsius.
    
    .. image:: _static/BB_cmap/cm_tmp.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    levels : int or None
        Number of discreate color levels. If None, cmap is continuous.
    """
    label = 'Temperature (C)'
    
    # Color tuple for every bin
    COLORS = [
        '#91003f', '#ce1256', '#e7298a', '#df65b0',
        '#ff73df', '#ffbee8', '#ffffff', '#dadaeb',
        '#bcbddc', '#9e9ac8', '#756bb1', '#54278f',
        '#0d007d', '#0d3d9c', '#0066c2', '#299eff',
        '#4ac7ff', '#73d7ff', '#adffff', '#30cfc2',
        '#009996', '#125757', '#066d2c', '#31a354',
        '#74c476', '#a1d99b', '#d3ffbe', '#ffffb3',
        '#ffeda0', '#fed176', '#feae2a', '#fd8d3c',
        '#fc4e2a', '#e31a1c', '#b10026', '#800026',
        '#590042', '#280028'
    ]

    if levels is None:
        cmap = colors.LinearSegmentedColormap.from_list("Temperature", COLORS)
    else:
        cmap = colors.LinearSegmentedColormap.from_list("Temperature",
                                                        COLORS, N=levels)
    norm = colors.Normalize(-50, 50)
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       extend='both')
    
    return {'cmap': cmap, 'norm': norm}, {'label': label, 'extend':'both'}

def cm_dpt(display_cmap=False):
    """
    Colormap for dew point temperature in Celsius.
    
    .. image:: _static/BB_cmap/cm_dpt.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    """
    label = 'Dew Point Temperature (C)'
    
    # Color tuple for every bin
    COLORS = [
        '#3b2204', '#543005', '#8c520a', '#bf812d',
        '#cca854', '#dfc27d', '#e6d9b5', '#d3ebe7',
        '#a9dbd3', '#72b8ad', '#318c85', '#01665f',
        '#003c30', '#002921'
    ]

    bounds = np.array([-10, 0, 10, 20, 30, 40, 45, 50, 
                       55, 60, 65, 70, 75, 80])
    
    cmap = colors.LinearSegmentedColormap.from_list("Dew Point", COLORS,
                                                    N=len(COLORS)+1)
    
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       ticks=bounds, spacing='proportional',
                                       extend='both')
    
    return {'cmap': cmap, 'norm': norm}, \
           {'label': label, 'ticks': bounds, 'spacing': 'proportional', 'extent':'both'}

def cm_rh(display_cmap=False):
    """
    Colormap for relative humidity as a percentage (0-100 %).
    
    .. image:: _static/BB_cmap/cm_rh.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    """
    label = 'Relative Humidity (%)'
    
    # Color tuple for every bin
    COLORS = [
        '#910022', '#a61122', '#bd2e24', '#d44e33',
        '#e36d42', '#fa8f43', '#fcad58', '#fed884',
        '#fff2aa', '#e6f49d', '#bce378', '#71b55c',
        '#26914b', '#00572e'
    ]

    bounds = [0,5,10,15,20,25,30,35,40,50,60,70,80,90, 100]
    
    cmap = colors.LinearSegmentedColormap.from_list("RH", COLORS,
                                                    N=len(COLORS))
    
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       ticks=bounds, spacing='proportional')
    
    return {'cmap': cmap, 'norm': norm}, \
           {'label': label, 'ticks': bounds, 'spacing': 'proportional'}
    
def cm_wind(display_cmap=False):
    """
    Colormap for wind speed (m/s).
    
    .. image:: _static/BB_cmap/cm_wind.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    """
    label = r'Wind Speed (m s$\mathregular{^{-1}}$)'
    
    # Color tuple for every bin
    COLORS = [
       '#103f78', '#225ea8', '#1d91c0', '#41b6c4',
       '#7fcdbb', '#b4d79e', '#dfff9e', '#ffffa6',
       '#ffe873', '#ffc400', '#ffaa00', '#ff5900',
       '#ff0000', '#a80000', '#6e0000', '#ffbee8',
       '#ff73df'
    ]

    bounds = np.array([0,5,10,15,20,25,30,35,40,45,50,60,70,80,100,120,140])
    
    cmap = colors.LinearSegmentedColormap.from_list("Wind Speed", COLORS,
                                                    N=len(COLORS)+1)
    
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       ticks=bounds, spacing='proportional',
                                       extend='max')
    
    return {'cmap': cmap, 'norm': norm}, \
           {'label': label, 'ticks': bounds, 'spacing': 'proportional', 'extend':'max'}
    

def cm_sky(display_cmap=False):
    """
    Colormap for sky/cloud cover (%).
    
    .. image:: _static/BB_cmap/cm_sky.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    """
    label = 'Cloud Cover (%)'
    
    # Color tuple for every bin
    COLORS = [
        '#24a0f2', '#4eb0f2', '#80b7f8', '#a0c8ff', '#d2e1ff',
        '#e1e1e1', '#c9c9c9', '#a5a5a5', '#6e6e6e', '#505050'
    ]

    bounds = np.arange(0,101,10)
    
    cmap = colors.LinearSegmentedColormap.from_list("Cloud Cover", COLORS,
                                                    N=len(COLORS))
    
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       ticks=bounds)
    
    return {'cmap': cmap, 'norm': norm}, \
           {'label': label, 'ticks': bounds}
    

def cm_precip(display_cmap=False, units='mm'):
    """
    Colormap for precipication (mm).
    
    .. image:: _static/BB_cmap/cm_precip.png
    
    Parameters
    ----------
    display_cmap : bool
        If True, show just the cmap
    units : {'mm', 'inches'}
        Specify units. Default is millimeters, but you might want to 
        show your graph in inches.
    """
       
    # Color tuple for every bin
    COLORS = [
        '#ffffff', '#c7e9c0', '#a1d99b', '#74c476', '#31a353', '#006d2c',
        '#fffa8a', '#ffcc4f', '#fe8d3c', '#fc4e2a', '#d61a1c', '#ad0026',
        '#700026', '#3b0030', '#4c0073', '#ffdbff'
    ]

    # These are in inches
    bounds = np.array([0,.01,.1,.25,.5,1,1.5,2,3,4,6,8,10,15,20,30])
    
    if units == 'mm':
        label = 'Precipication (mm)'
        bounds *= 25.4
    elif units == 'inches':
        label = 'Precipication (inches)'
    
    cmap = colors.LinearSegmentedColormap.from_list("Precipitation", COLORS,
                                                    N=len(COLORS)+1)
    norm = colors.BoundaryNorm(boundaries=bounds, ncolors=len(bounds))
    
    if display_cmap:
        fig = plt.figure(figsize=(8, 3))
        ax = fig.add_axes([0.05, 0.80, 0.9, 0.1])
        cb = mpl.colorbar.ColorbarBase(ax, orientation='horizontal', 
                                       cmap=cmap, norm=norm, label=label,
                                       ticks=bounds, extend='max')
    
    return {'cmap': cmap, 'norm': norm}, \
           {'label': label, 'ticks': bounds}
    
if __name__ == '__main__':
    # Make colorbars for docs
    
    from pathlib import Path
    IMG_DIR = Path('../../docs/_static/BB_cmap')
    if not IMG_DIR.is_dir():
        IMG_DIR.mkdir(parents=True)

    cm_tmp(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_tmp', bbox_inches='tight')
    
    cm_dpt(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_dpt', bbox_inches='tight')
    
    cm_rh(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_rh', bbox_inches='tight')
    
    cm_wind(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_wind', bbox_inches='tight')
    
    cm_sky(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_sky', bbox_inches='tight')
    
    cm_precip(display_cmap=True)
    plt.savefig(IMG_DIR / 'cm_precip', bbox_inches='tight')


    # Continuous Colorbar
    cm_tmp(display_cmap=True, levels=None)
    plt.savefig(IMG_DIR / 'cm_tmp_continuous', bbox_inches='tight')
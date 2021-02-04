
## Brian Blaylock
## February 3, 2021 

"""
Last copied Dec 14 2020

=============
Cartopy Tools
=============

General helpers for cartopy plots.

"""

import cartopy.crs as ccrs
import cartopy.feature as feature
import cartopy.io.img_tiles as cimgt
from shapely.geometry import Polygon

pc = ccrs.PlateCarree()

def check_cartopy_axes(ax=None, projection=pc, verbose=False):
    """
    Check an axes is a cartopy axes, else create a new cartopy axes.
    
    Parameters
    ----------
    ax : {None, cartopy.mpl.geoaxes.GeoAxesSubplot}
        If None, and plt.gca() is a cartopy axes, use it, 
        else create a new cartopy axes.
    """
    if ax is None:
        if hasattr(plt.gca(), 'coastlines'):
            if verbose: print('Using the current cartopy axes.')
            return plt.gca()  
        else:
            # Create a new cartopy axes
            if verbose: print('The current axes is not a cartopy axes. Create a new cartopy axes.')
            return plt.axes(projection=projection)
    else:
        if hasattr(ax, 'coastlines'):
            if verbose: print('The provided axes is a cartopy axes.')
            return ax
        else:
            raise TypeError('The `ax` you gave me is not a cartopy axes')

def common_features(scale='110m', counties_scale='20m', figsize=None, *,
                    ax=None, projection=pc, verbose=False,
                    dark_theme=False,                    
                    COASTLINES=True, BORDERS=False,
                    STATES=False, COUNTIES=False, 
                    OCEAN=False, LAND=False,
                    RIVERS=False, LAKES=False, 
                    STAMEN=False,
                    COASTLINES_kwargs={}, BORDERS_kwargs={},
                    STATES_kwargs={}, COUNTIES_kwargs={},
                    OCEAN_kwargs={}, LAND_kwargs={},
                    RIVERS_kwargs={}, LAKES_kwargs={},
                    STAMEN_kwargs={},
                    **kwargs):
    """
    Add common features to a cartopy axis. 
    
    .. Tip:: This is a great way to initialize a new cartopy axes.

    Parameters
    ----------
    scale : {'10m', '50m' 110m'}
        The cartopy feature's level of detail
        
        .. note:: 
            The ``'10m'`` scale for OCEAN and LAND takes a *long* time.
            Consider using ``'50m'`` if you need OCEAN and LAND colored.           
    
    counties_scale: {'20m', '5m', '500k'}
        Counties are plotted via MetPy and have different resolutions 
        available than other features.
        -  20m = 20,000,000 resolution (Ok if you show a large area)
        -   5m =  5,000,000 resolution (provides good detail)
        - 500k =    500,000 resolution (plots very slow)
    
    ax : plot axes
        The axis to add the feature to.
        If None, it will create a new cartopy axes with ``projection``.
    projection : cartopy.crs
        Projection to create new map if no cartopy axes is given.
        Default is PlateCarree.
    dark_theme : bool
        If True, use alternative "dark theme" colors for land and water.
        
        .. figure:: _static/BB_maps/common_features-1.png
        .. figure:: _static/BB_maps/common_features-2.png

    FEATURES : bool
        Toggle on various features. By default, only COASTLINES is
        turned on. Each feature has a cooresponding ``FEATURE_kwargs={}``
        dictionary to supply additional arguments to cartopy's add_feature
        method (e.g., change line color or width by feature type).

    ========== =========================================================
    FEATURE    Description
    ========== =========================================================
    COASTLINES Coastlines, boundary between land and ocean.
    BORDERS    Borders between countries. *Does not includes coast*.
    STATES     US state borders. Includes coast.
    COUNTIES   US Counties. Includes coast.
    OCEAN      Colored ocean area
    LAND       Colored land area
    RIVERS     Lines where rivers exist
    LAKES      Colored lake area
    ========== =========================================================
    
    ========== =========================================================
    MAP TILE   Description
    ========== =========================================================
    Stamen     Specify type and zoom level. http://maps.stamen.com/
               Style: ``terrain-background``, ``terrain``, 
                      ``toner-background``, ``toner``, `watercolor``
               Zoom: int [0-10]

    Examples
    --------
    https://inversion.nrlmry.navy.mil/confluence/display/~Blaylock/2020/08/07/Cartopy%3A+Add+Common+Features
    
    Each feature can be toggled on by setting the argument to ``True``.
    
    .. figure:: _static/BB_maps/individual_features.png
    
    By default, the COASTLINES=True
    
    .. figure:: _static/BB_maps/features_with_coastlines.png
    .. figure:: _static/BB_maps/features_with_coastlines_DARK.png
    
    The next two illustrate the level of detail for ``'50m'`` and ``'10m'``.
    Note that the OCEAN and LAND features take 3+ minutes to render for the
    10m resolution the first time you plot it. 
    
    .. figure:: _static/BB_maps/features_with_coastlines_10m.png
    .. figure:: _static/BB_maps/features_with_coastlines_50m.png
    
    Returns
    -------
    The cartopy axes (obviously you don't need this if you gave an ax
    as an argument, but it is useful if you initialize a new map).
    """
    ax = check_cartopy_axes(ax, projection)
    
    if (LAND or OCEAN) and scale in ['10m']:
        warnings.warn('🕖 OCEAN or LAND features at 10m will take a long time (3+ mins) to display.')
    
    kwargs.setdefault('linewidth', .75)
    
    COASTLINES_kwargs = {**dict(zorder=100, facecolor='none'), **COASTLINES_kwargs}
    COUNTIES_kwargs = {**{'linewidth': .5}, **COUNTIES_kwargs}
    LAND_kwargs = {**{'edgecolor': 'none'}, **LAND_kwargs}
    OCEAN_kwargs = {**{'edgecolor': 'none'}, **OCEAN_kwargs}
    LAKES_kwargs = {**{'linewidth': 0}, **LAKES_kwargs}
    
    if dark_theme:
        kwargs = {**kwargs, **{'edgecolor':'.5'}}
        land = '#060613'
        water = '#0f2b38'
        LAND_kwargs = {**{'facecolor': land}, **LAND_kwargs}
        OCEAN_kwargs = {**{'facecolor': water}, **OCEAN_kwargs}
        RIVERS_kwargs = {**{'edgecolor': water}, **RIVERS_kwargs}
        LAKES_kwargs = {**{'facecolor': water}, **LAKES_kwargs}
        #https://github.com/SciTools/cartopy/issues/880
        ax.background_patch.set_facecolor(land) # depreciated
        #ax.set_facecolor(land) # Might work if I update cartopy
    else:
        kwargs = {**kwargs, **{'edgecolor':'.15'}}
        RIVERS_kwargs = {**{'edgecolor': feature.COLORS['water']}, **RIVERS_kwargs}
    
    ##------------------------------------------------------------------
    ## Add each element to the plot
    ## When combining kwargs, 
    ##  - kwargs is the main value
    ##  - FEATURE_kwargs is the overwrite for the feature
    ## For example:
    ##     {**kwargs, **FEATURE_kwargs}
    ## the kwargs are overwritten by FEATURE kwargs
    ##------------------------------------------------------------------

    if COASTLINES: 
        #ax.coastlines(scale, **kwargs)  # Nah, use the crs.feature instead
        ax.add_feature(feature.COASTLINE.with_scale(scale),
                       **{**kwargs, **COASTLINES_kwargs})
    if BORDERS: 
        ax.add_feature(feature.BORDERS.with_scale(scale),
                       **{**kwargs, **BORDERS_kwargs})
    if STATES: 
        ax.add_feature(feature.STATES.with_scale(scale),
                       **{**kwargs, **STATES_kwargs})
    if COUNTIES:
        _counties_scale = {'20m', '5m', '500k'}
        assert counties_scale in _counties_scale, f"counties_scale must be {_counties_scale}"
        ax.add_feature(USCOUNTIES.with_scale(counties_scale),
                       **{**kwargs, **COUNTIES_kwargs})
    if OCEAN: 
        ax.add_feature(feature.OCEAN.with_scale(scale),
                       **{**kwargs, **OCEAN_kwargs})
    if LAND and not dark_theme:
        # If `dark_theme=True`, the face_color is the land color.
        ax.add_feature(feature.LAND.with_scale(scale), 
                       **{**kwargs, **LAND_kwargs})
    if RIVERS: 
        ax.add_feature(feature.RIVERS.with_scale(scale),
                       **{**kwargs, **RIVERS_kwargs})
    if LAKES: 
        ax.add_feature(feature.LAKES.with_scale(scale),
                       **{**kwargs, **LAKES_kwargs})
    
    if STAMEN:
        if verbose: print("Please use `ax.set_extent` before increasing Zoom level.")
        STAMEN_kwargs.setdefault('style', 'terrain-background')
        STAMEN_kwargs.setdefault('zoom', 3)
        style = STAMEN_kwargs['style']
        zoom = STAMEN_kwargs['zoom']
        stamen_terrain = cimgt.Stamen(style)
        ax.add_image(stamen_terrain, zoom)

        if 'alpha' in STAMEN_kwargs:
            # Need to manually put a white layer over the STAMEN terrain
            STAMEN_kwargs.setdefault('alpha_color', 'w')
            poly = ax.projection.domain
            ax.add_feature(feature.ShapelyFeature([poly], ax.projection),
                           color=STAMEN_kwargs['alpha_color'], 
                           alpha=1-STAMEN_kwargs['alpha'], 
                           zorder=1)

    if figsize is not None:
        plt.gcf().set_figwidth(figsize[0])
        plt.gcf().set_figheight(figsize[1])

    return ax

def domain_border(x, y=None, *, ax=None, text=None,
                  method='cutout', verbose=False,
                  facealpha=.25,
                  text_kwargs={}, **kwargs):
    """
    Add a polygon of the domain boundary to a map.

    The border is drawn from the outside values of the latitude and 
    longitude xarray coordinates or numpy array. 
    Lat/lon values should be given as degrees.

    Parameters
    ----------
        x : xarray.Dataset or numpy.ndarray
            If xarray, then should contain 'latitude' and 'longitude' coordinate.
            If numpy, then 2D numpy array for longitude and `y` arg is required.
        y : numpy.ndarray
            Only required if x is a numpy array.
            A numpy array of latitude values.
        ax : cartopy axis
            The axis to add the border to.
            Default None and will get the current axis (will create one).
        text : str
            If not None, puts the string in the bottom left.
        method : {'fill', 'cutout', 'border'}
            Plot the domain as a filled area Polygon, a Cutout from the
            map, or as a simple border.
        facealpha : float between 0 and 1
            Since there isn't a "facealpha" attribute for plotting,
            this will be it.

    Returns
    -------
    Adds a boarder around domain to the axis and returns the artist.
    """
    if hasattr(x, 'crs'):
        ax = check_cartopy_axes(ax, projection=x.crs)
        if verbose: print(f'crs is {x.crs}')
    else:
        print('crs is not in the xarray.Dataset')
        ax = check_cartopy_axes(ax)
    
    _method =  {'cutout', 'fill', 'border'}
    assert method in _method, f"Method must be one of {_method}."
    
    ####################################################################
    # Determine how to handle output...xarray or numpy
    if isinstance(x, (xr.core.dataset.Dataset, \
                      xr.core.dataarray.DataArray)):
        if verbose: print("process input as xarray")
        
        if 'latitude' in x.coords:
            x = x.rename({'latitude': 'lat',
                          'longitude': 'lon'})
        LON = x.lon.data
        LAT = x.lat.data
    
    elif isinstance(x, np.ndarray):
        assert y is not None, "Please supply a value for x and y"
        if verbose: print("process input as numpy array")
        LON = x
        LAT = y 
    else:
        raise ValueError("Review your input")
    ####################################################################
    
    # Path of array outside border starting from the lower left corner
    # and going around the array counter-clockwise.
    outside = list(zip(LON[0, :], LAT[0, :])) \
            + list(zip(LON[:, -1], LAT[:, -1])) \
            + list(zip(LON[-1, ::-1], LAT[-1, ::-1])) \
            + list(zip(LON[::-1, 0], LAT[::-1, 0]))
    outside = np.array(outside)
    
    ## Polygon in latlon coordinates
    ## -----------------------------
    x = outside[:, 0]
    y = outside[:, 1]
    domain_polygon_latlon = Polygon(zip(x, y))    
    
    ## Polygon in projection coordinates
    ## ----------------------------------
    transform = ax.projection.transform_points(pc, x, y)
    
    # Remove any points that run off the projection map (i.e., point's value is `inf`).
    transform = transform[~np.isinf(transform).any(axis=1)]
    
    # These are the x and y points we need to create the Polygon for
    x = transform[:, 0]
    y = transform[:, 1]
    
    domain_polygon = Polygon(zip(x, y))    # This is the boundary of the LAT/LON array supplied.
    global_polygon = ax.projection.domain  # This is the projection globe polygon
    cutout = global_polygon.difference(domain_polygon)  # This is the differencesbetween the domain and glob polygon
    
    # Plot
    kwargs.setdefault('edgecolors', 'k')
    kwargs.setdefault('linewidths', 1)
    if method=='fill':
        kwargs.setdefault('facecolor', (0,0,0,facealpha))
        artist = ax.add_feature(feature.ShapelyFeature([domain_polygon], ax.projection), **kwargs)
    elif method=='cutout':
        kwargs.setdefault('facecolor', (0,0,0,facealpha))
        artist = ax.add_feature(feature.ShapelyFeature([cutout], ax.projection), **kwargs)
    elif method=='border':
        kwargs.setdefault('facecolor', 'none')
        artist = ax.add_feature(feature.ShapelyFeature([domain_polygon.exterior], ax.projection), **kwargs)
        
    if text:
        text_kwargs.setdefault('verticalalignment', 'bottom')
        text_kwargs.setdefault('fontsize', 15)
        xx, yy = outside[0]
        ax.text(xx+.2, yy+.2, text, transform=pc, **text_kwargs)

    return artist, domain_polygon, domain_polygon_latlon

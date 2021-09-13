## Brian Blaylock
## September 28, 2020

"""
==========================
Tools for the HRRR Archive
==========================

to_180
    For longitude values to be from -180 W to 180 E (not 0-360 E).
get_crs
    Get cartopy projection object from xarray.Dataset
pluck_points
    Pluck values at specific latitude/longitude points.
"""

import multiprocessing

import cartopy.crs as ccrs
import numpy as np
import xarray as xr

import hrrrb.archive as ha


def to_180(lon):
    """
    Wrap longitude from degrees [0, 360] to degrees [-180, 180].

    An alternative method is
        lon[lon>180] -= 360

    Parameters
    ----------
    lon : array_like
        Longitude values
    """
    lon = np.array(lon)
    lon = (lon + 180) % 360 - 180
    return lon

def get_crs(ds):
    """
    Get the cartopy coordinate reference system (crs) from a cfgrib xarray Dataset

    Projection in formation is from the grib2 message for each variable.

    Parameters
    ----------
    ds : xarray.Dataset
        An xarray.Dataset from a GRIB2 file opened by the cfgrib engine.
    """
    # Get projection from the attributes of HRRR xr.Dataset
    # CF 1.8 map projection information for the HRRR model
    # http://cfconventions.org/Data/cf-conventions/cf-conventions-1.8/cf-conventions.html#_lambert_conformal


    if isinstance(ds, list):
        # The case when get_hrrr returns a list of xr.Datasets
        return get_crs(ds[0])


    if isinstance(ds, xr.Dataset):
        attrs = ds[list(ds)[0]].attrs
    if isinstance(ds, xr.DataArray):
        attrs = ds.attrs
    if attrs['GRIB_gridType'] == 'lambert':
        lc_hrrr_kwargs = {
            'globe': ccrs.Globe(ellipse='sphere'),
            'central_latitude': attrs['GRIB_LaDInDegrees'],
            'central_longitude': attrs['GRIB_LoVInDegrees'],
            'standard_parallels': (attrs['GRIB_Latin1InDegrees'],\
                                   attrs['GRIB_Latin2InDegrees'])}
        lc = ccrs.LambertConformal(**lc_hrrr_kwargs)
        return lc
    else:
        warnings.warn('GRIB_gridType is not "lambert".')
        return None

def pluck_points(ds, points, names=None, dist_thresh=10_000, verbose=True):
    """
    Pluck values at point nearest a give list of latitudes and longitudes pairs.

    Uses a nearest neighbor approach to get the values. The general
    methodology is illustrated in this
    `GitHub Notebook <https://github.com/blaylockbk/pyBKB_v3/blob/master/demo/Nearest_lat-lon_Grid.ipynb>`_.

    Parameters
    ----------
    ds : xarray.Dataset
        The Dataset should include coordinates for both 'latitude' and
        'longitude'.
    points : tuple or list of tuples
        The latitude and longitude (lat, lon) coordinate pair (as a tuple)
        for the points you want to pluck from the gridded Dataset.
        A list of tuples may be given to return the values from multiple points.
    names : list
        A list of names for each point location (i.e., station name).
        None will not append any names. names should be the same
        length as points.
    dist_thresh: int or float
        The maximum distance (m) between a plucked point and a matched point.
        Default is 10,000 m. If the distance is larger than this, the point
        is disregarded.

    Returns
    -------
    The Dataset values at the points nearest the requested lat/lon points.
    """
    if 'lat' in ds:
        ds = ds.rename(dict(lat='latitude', lon='longitude'))

    if isinstance(points, tuple):
        # If a tuple is give, turn into a one-item list.
        points = [points]

    if names is not None:
        assert len(points) == len(names), '`points` and `names` must be same length.'

    # Find the index for the nearest points
    xs = []  # x index values
    ys = []  # y index values
    for point in points:
        assert len(point) == 2, "``points`` should be a tuple or list of tuples (lat, lon)"

        p_lat, p_lon = point

        # Force longitude values to range from -180 to 180 degrees.
        p_lon = to_180(p_lon)
        ds['longitude'][:] = to_180(ds.longitude)

        # Find absolute difference between requested point and the grid coordinates.
        abslat = np.abs(ds.latitude - p_lat)
        abslon = np.abs(ds.longitude - p_lon)

        # Create grid of the maximum values of the two absolute grids
        c = np.maximum(abslon, abslat)

        # Find location where lat/lon minimum absolute value intersects
        if ds.latitude.dims == ('y', 'x'):
            y, x = np.where(c == np.min(c))
        elif ds.latitude.dims == ('x', 'y'):
            x, y = np.where(c == np.min(c))
        else:
            raise ValueError(f"Sorry, I do not understand dimensions {ds.latitude.dims}. Expected ('y', 'x')" )
        xs.append(x[0])
        ys.append(y[0])

    #===================================================================
    # Select Method 1:
    # This method works, but returns more data than you ask for.
    # It returns an NxN matrix where N is the number of points,
    # and matches each point with each point (not just the coordinate
    # pairs). The points you want will be along the diagonal.
    # I leave this here so I remember not to do this.
    #
    #ds = ds.isel(x=xs, y=ys)
    #
    #===================================================================

    #===================================================================
    # Select Method 2:
    # This is only *slightly* slower, but returns just the data at the
    # points you requested. Creates a new dimension, called 'point'
    ds = xr.concat([ds.isel(x=i, y=j) for i, j in zip(xs, ys)], dim='point')
    #===================================================================

    #-------------------------------------------------------------------
    # 📐Approximate the Great Circle distance between matched point and
    # requested point.
    # Based on https://andrew.hedges.name/experiments/haversine/
    #-------------------------------------------------------------------
    lat1 = np.deg2rad([i[0] for i in points])
    lon1 = np.deg2rad([i[1] for i in points])

    lat2 = np.deg2rad(ds.latitude.data)
    lon2 = np.deg2rad(ds.longitude.data)

    R = 6373.0 # approximate radius of earth in km

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c * 1000  # converted to meters

    # Add the distance values as a coordinate
    ds.coords['distance'] = ('point', distance)
    ds['distance'].attrs = dict(long_name='Distance between requested point and matched grid point', units='m')

    #-------------------------------------------------------------------
    #-------------------------------------------------------------------

    # Add list of names as a coordinate
    if hasattr(names, '__len__'):
        # Assign the point dimension as the names.
        assert len(ds.point) == len(names), f'`names` must be same length as `points` pairs.'
        ds['point'] = names

    ## Print some info about each point:
    if verbose:
        zipped = zip([i[0] for i in points], [i[1] for i in points],
                     ds.latitude.data, ds.longitude.data, ds.distance.data, ds.point.data)
        for plat, plon, glat, glon, d, name in zipped:
            print(f"🔎 Matched requested point [{name}] ({plat:.3f}, {plon:.3f}) to grid point ({glat:.3f}, {glon:.3f})...distance of {d/1000:,.2f} km.")
            if d > dist_thresh:
                print(f'   💀 Point [{name}] Failed distance threshold')

    ds.attrs['x_index'] = xs
    ds.attrs['y_index'] = ys

    # Drop points that do not meet the dist_thresh criteria
    failed = ds.distance < dist_thresh
    print(len(failed), failed.data)
    warnings.warn(f' 💀 Dropped {np.sum(failed).data} point(s) that exceeded dist_thresh.')
    ds = ds.where(failed, drop=True)

    return ds

#=======================================================================
#=======================================================================

## WORK IN PROGRESS 🏗

# A method to download multiple forecasts and read into xarray
def _concat_hrrr(inputs):
    """Multiprocessing Helper"""
    DATE, searchString, fxx, kwargs = inputs
    return ha.xhrrr(DATE, searchString, fxx=fxx, **kwargs)

def concat_hrrr(DATES, searchString, fxxs=range(19), **get_hrrr_kwargs):
    """
    Download variables
    """
    inputs = [(DATE, searchString, f, get_hrrr_kwargs) for f in fxxs]

    cores = np.minimum(len(inputs), multiprocessing.cpu_count())
    print('cores=', cores)

    with multiprocessing.Pool(cores) as p:
        result = p.map(_concat_hrrr, inputs)
        p.close()
        p.join()

    return xr.concat(result, dim='lead')


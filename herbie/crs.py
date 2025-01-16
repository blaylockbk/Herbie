"""Parse CF coordinate reference system (CRS)."""

from pyproj import CRS


def parse_cf_crs(ds, variable=None):
    """Parse CF coordinate reference system (CRS) from a xarray dataset."""
    if variable is None:
        variable = next(iter(ds.data_vars))
    da = ds[variable]

    # Shape of the Earth reference system
    # https://codes.ecmwf.int/grib/format/grib2/ctables/3/2/
    shapeOfTheEarth = da.GRIB_shapeOfTheEarth
    if shapeOfTheEarth == 0:
        # Earth assumed spherical with radius = 6 367 470.0 m
        a = 6_367_470
        b = 6_367_470
    elif shapeOfTheEarth == 1:
        # Earth assumed spherical with radius specified (in m) by data producer
        # TODO: Why is model='graphcast' using this value?
        a = 4326.0
        b = 4326.0
    elif shapeOfTheEarth == 6:
        # Earth assumed spherical with radius of 6,371,229.0 m
        a = 6_371_229
        b = 6_371_229

    if da.GRIB_gridType == "lambert":
        projparams = {"proj": "lcc"}
        projparams["a"] = a
        projparams["b"] = b
        projparams["lon_0"] = da.GRIB_LoVInDegrees
        projparams["lat_0"] = da.GRIB_LaDInDegrees
        projparams["lat_1"] = da.GRIB_Latin1InDegrees
        projparams["lat_2"] = da.GRIB_Latin2InDegrees

    elif da.GRIB_gridType == "regular_ll":
        projparams = {"proj": "latlong"}
        projparams["a"] = a
        projparams["b"] = b

    elif da.GRIB_gridType == "polar_stereographic":
        projparams = {"proj": "stere"}
        projparams["a"] = a
        projparams["b"] = b
        projparams["lat_ts"] = da.GRIB_LaDInDegrees
        projparams["lat_0"] = 90
        projparams["lon_0"] = da.GRIB_orientationOfTheGridInDegrees

    else:
        raise NotImplementedError(f"gridType {da.GRIB_gridType} is not implemented.")

    return CRS(projparams).to_cf()


"""
with pygrib.open(str(ds.local_grib)) as grb:
    msg = grb.message(1)
    print(msg.projparams)

Also, look at all keys with:
grib_dump -j <filename.grib2> > filedump.json

HRRR
{'a': 6371229,
 'b': 6371229,
 'proj': 'lcc',
 'lon_0': 262.5,
 'lat_0': 38.5,
 'lat_1': 38.5,
 'lat_2': 38.5}

HRRR-Alaska
{'a': 6371229,
 'b': 6371229,
 'proj': 'stere',
 'lat_ts': 60.0,
 'lat_0': 90.0,
 'lon_0': 225.0}

GFS
{'a': 6371229, 'b': 6371229, 'proj': 'longlat'}

NAM
{'a': 6371229,
 'b': 6371229,
 'proj': 'lcc',
 'lon_0': 262.5,
 'lat_0': 38.5,
 'lat_1': 38.5,
 'lat_2': 38.5}
"""

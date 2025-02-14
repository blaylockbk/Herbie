"""CF convention coordinate reference system (CRS).

Check out the notebook `check_pygrib_vs_herbie_crs_extraction.ipynb`
to test how Herbie and pygrib are extracting the CRS information.
"""

from typing import Any

from pyproj import CRS

import xarray as xr


def get_cf_crs(
    ds: "xr.Dataset",
    variable: str | None = None,
    *,
    use_pygrib: bool = False,
    _return_projparams: bool = False,
) -> dict:
    """
    Extract the CF coordinate reference system (CRS) from a cfgrib xarray dataset.

    Note:
    I originally used pygrib to do this, but it was hard to maintain an
    additional grib package dependency. I had issues with pygrib after
    it was updated to support Numpy version 2, so thought it would be
    best to code this in Herbie. This may be incomplete.


    Parameters
    ----------
    ds : xr.Dataset
        An xarray dataset with cfgrib variables.
    variable : str, optional
        The variable to extract the CRS from. If None, the first variable
        in the dataset will be used. Default is None.
    use_pygrib : bool, optional
        Use pygrib to extract the CRS. Default is False.
    _return_projparams : bool, optional
        Return the projparams dictionary instead of the CF dictionary.
        Default is False.
    """
    if use_pygrib:
        # Get CF grid projection information with pygrib and pyproj because
        # this is something cfgrib doesn't do (https://github.com/ecmwf/cfgrib/issues/251)
        import pygrib

        with pygrib.open(ds.attrs['local_file']) as grb:
            msg = grb.message(1)
            projparams = msg.projparams

        # Funny stuff with polar stereographic (https://github.com/pyproj4/pyproj/issues/856)
        # TODO: Is there a better way to handle this? What about south pole?
        #if cf_params["grid_mapping_name"] == "polar_stereographic":
        #    cf_params["latitude_of_projection_origin"] = cf_params.get(
        #        "latitude_of_projection_origin", 90
        #    )
        
    else:
        # Assume the first variable in the Dataset has the same grid crs
        # as all other variables in the Dataset.
        if variable is None:
            variable = next(iter(ds.data_vars))
        da = ds[variable]

        # Shape of the Earth reference system
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/2/
        shapeOfTheEarth = da.GRIB_shapeOfTheEarth
        match shapeOfTheEarth:
            case 0:
                # Earth assumed spherical with radius = 6 367 470.0 m
                a = 6_367_470
                b = 6_367_470
            case 1 if ds.attrs["model"] == "graphcast":
                # Earth assumed spherical with radius specified (in m) by data producer
                # TODO: Why is model='graphcast' using this value?
                a = 4_326.0
                b = 4_326.0
            case 1 if ds.attrs["model"] in ["urma", "rtma"]:
                # Earth assumed spherical with radius specified (in m) by data producer
                # TODO: Why is urma and rtma using this value?
                a = 6_371_200.0
                b = 6_371_200.0
            case 6:
                # Earth assumed spherical with radius of 6,371,229.0 m
                a = 6_371_229
                b = 6_371_229
            case _:
                raise ValueError(
                    f"Unsupported parameters {shapeOfTheEarth=} {ds.attrs.get('model')=}"
                )

        # Grid type definition
        # https://codes.ecmwf.int/grib/format/grib2/ctables/3/1/
        match da.GRIB_gridType:
            case "lambert":
                projparams = {"proj": "lcc"}
                projparams["a"] = a
                projparams["b"] = b
                projparams["lon_0"] = da.GRIB_LoVInDegrees
                projparams["lat_0"] = da.GRIB_LaDInDegrees
                projparams["lat_1"] = da.GRIB_Latin1InDegrees
                projparams["lat_2"] = da.GRIB_Latin2InDegrees

            case "regular_ll" | "regular_gg":
                projparams = {"proj": "longlat"}
                projparams["a"] = a
                projparams["b"] = b

            case "polar_stereographic":
                projparams = {"proj": "stere"}
                projparams["a"] = a
                projparams["b"] = b
                projparams["lat_ts"] = da.GRIB_LaDInDegrees
                projparams["lat_0"] = 90
                projparams["lon_0"] = da.GRIB_orientationOfTheGridInDegrees

            case _:
                raise NotImplementedError(
                    f"gridType {da.GRIB_gridType} is not implemented."
                )

    if _return_projparams:
        return projparams
    else:
        return CRS(projparams).to_cf()


"""
Look at how pygrib parses with this...
with pygrib.open(str(ds.local_grib)) as grb:
    msg = grb.message(1)
    print(msg.projparams)

Also, look for clues by dumping all keys with:
grib_dump -j <filename.grib2> > filedump.json

-----------------------------------------

Model: HRRR
  pygrib {'a': 6371229, 'b': 6371229, 'lat_0': 38.5, 'lat_1': 38.5, 'lat_2': 38.5, 'lon_0': 262.5, 'proj': 'lcc'}
  Herbie {'a': 6371229, 'b': 6371229, 'lat_0': 38.5, 'lat_1': 38.5, 'lat_2': 38.5, 'lon_0': 262.5, 'proj': 'lcc'}
  equal= True

Model: HRRRAK
  pygrib {'a': 6371229, 'b': 6371229, 'lat_0': 90.0, 'lat_ts': 60.0, 'lon_0': 225.0, 'proj': 'stere'}
  Herbie {'a': 6371229, 'b': 6371229, 'lat_0': 90, 'lat_ts': 60.0, 'lon_0': 225.0, 'proj': 'stere'}
  equal= True

Model: GFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: GRAPHCAST
  pygrib {'a': 4326.0, 'b': 4326.0, 'proj': 'longlat'}
  Herbie {'a': 4326.0, 'b': 4326.0, 'proj': 'longlat'}
  equal= True

Model: CFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: IFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: AIFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: GEFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: GEFS
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: HAFSA
  pygrib {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  Herbie {'a': 6371229, 'b': 6371229, 'proj': 'longlat'}
  equal= True

Model: HREF
  pygrib {'a': 6371229, 'b': 6371229, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  Herbie {'a': 6371229, 'b': 6371229, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  equal= True

Model: NAM
  pygrib {'a': 6371229, 'b': 6371229, 'lat_0': 38.5, 'lat_1': 38.5, 'lat_2': 38.5, 'lon_0': 262.5, 'proj': 'lcc'}
  Herbie {'a': 6371229, 'b': 6371229, 'lat_0': 38.5, 'lat_1': 38.5, 'lat_2': 38.5, 'lon_0': 262.5, 'proj': 'lcc'}
  equal= True

Model: URMA
  pygrib {'a': 6371200.0, 'b': 6371200.0, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  Herbie {'a': 6371200.0, 'b': 6371200.0, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  equal= True

Model: RTMA
  pygrib {'a': 6371200.0, 'b': 6371200.0, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  Herbie {'a': 6371200.0, 'b': 6371200.0, 'lat_0': 25.0, 'lat_1': 25.0, 'lat_2': 25.0, 'lon_0': 265.0, 'proj': 'lcc'}
  equal= True
"""

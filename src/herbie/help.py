"""Some help messages from Herbie."""


def _search_help(kind="wgrib2"):
    """Help/Error Message for `search` argument.

    Parameters
    ----------
    kind : {"wgrib2", "eccodes"}
        There are two different utilities used to create index files and
        they create different file output.

        - **wgrib2** is the NCEP-style grib messages
        - **eccodes** is the ECMWF-style grib messages
    """
    if kind == "wgrib2":
        msg = r"""
Use regular expression to search for lines in the index file.
Here are some examples you can use for the wgrib2-style `search`

    ==================================== ==========================================================
    search=                              GRIB messages that will be downloaded
    ==================================== ==========================================================
    ":TMP:2 m"                           Temperature at 2 m.
    ":TMP:"                              Temperature fields at all levels.
    ":UGRD:\d+ mb"                       U Wind at all pressure levels.
    ":500 mb:"                           All variables on the 500 mb level.
    ":APCP:"                             All accumulated precipitation fields.
    ":APCP:surface:0-[1-9]*"             Accumulated precip since initialization time
    ":APCP:.*:(?:0-1|[1-9]\d*-\d+) hour" Accumulated precip over last hour
    ":UGRD:10 m"                         U wind component at 10 meters.
    ":[U|V]GRD:[1,8]0 m"                 U and V wind component at 10 and 80 m.
    ":[U|V]GRD:"                         U and V wind component at all levels.
    ":.GRD:"                             (Same as above)
    ":[U|V]GRD:\d+ hybrid"               U and V wind components at all hybrid levels
    ":[U|V]GRD:\d+ mb"                   U and V wind components at all pressure levels
    ":(?:TMP|DPT):"                      Temperature and Dew Point for all levels .
    ":(?:TMP|DPT|RH):"                   TMP, DPT, and Relative Humidity for all levels.
    ":REFC:"                             Composite Reflectivity
    ":surface:"                          All variables at the surface.
    "^TMP:2 m.*fcst$"                    Beginning of string (^), end of string ($) wildcard (.*)
    ==================================== ==========================================================

If you need help with regular expression, search the web or look at
this cheatsheet: https://www.petefreitag.com/cheatsheets/regex/.

Here is an example: https://regex101.com/r/1Dku20/1
"""

    elif kind == "eccodes":
        msg = r"""
Use regular expression to search for lines in the index file.
Here are some examples you can use for the ecCodes-style `search`

Look at the ECMWF GRIB Parameter Database
https://apps.ecmwf.int/codes/grib/param-db


product=`oper` or `enfo`
======================== ==============================================
search=                  GRIB messages that will be downloaded
======================== ==============================================
":2t:"                   2-m temperature
":2d:"                   2-m dew point temperature
":10u:"                  10-m u wind vector
":10v:"                  10-m v wind vector
":10[uv]:                10-m u and 10-m v wind
":[tuvr]:"               Temp, u/v wind, RH (all levels)
":500:"                  All variables on the 500 hPa level
":gh:500"                Geopotential height only at 500 hPa
":gh:"                   Geopotential height (all pressure levels)
":t:"                    Temperature (all pressure levels)
":q:"                    Specific Humidity (all pressure levels)
":r:"                    Relative humidity (all pressure levels)
":v:"                    v wind vector (all pressure levels)
":u:"                    u wind vector (all pressure levels)
":w:"                    Vertical velocity (Pascals per second)
":lsm:"                  Land-sea mask
":ttr:"                  Top net long-wave (thermal) radiation
":ssrd:"                 Surface short-wave (solar) radiation downwards
":ssr:"                  Surface net short-wave (solar) radiation
":strd:"                 Surface long-wave (thermal) radiation downwards
":str:"                  Surface net long-wave (thermal) radiation
":swvl1:"                Volumetric soil water layer 1 (depth 0 meters)
":swvl2:"                Volumetric soil water layer 2 (depth 7 meters)
":swvl3:"                Volumetric soil water layer 3 (depth 28 meters)
":swvl4:"                Volumetric soil water layer 4 (depth 100 meters)
":skt:"                  Skin (surface) temperature
":d:"                    Divergence (all levels)
":st:"                   Soil temperature
":stl2:"                 Soil temperature level 2 (depth 7 meters)
":tp:"                   Total precipitation
":ro:"                   Run-off
":asn:"                  Snow albedo
":msl:"                  Mean sea level pressure
":sp:"                   Surface pressure
":cape:"                 CAPE
":tcwv:"                 Total column vertically integrated water vapor
":vo:"                   Relative vorticity

product=`wave` or `waef`
======================== ==============================================
search=                  GRIB messages that will be downloaded
======================== ==============================================
":swh:"                  Significant height of wind waves + swell
":mwp:"                  Mean wave period
":mwd:"                  Mean wave direction
":pp1d:"                 Peak wave period
":mp2:"                  Mean zero-crossing wave period

If you need help with regular expression, search the web or look at
this cheatsheet: https://www.petefreitag.com/cheatsheets/regex/.

Here is an example: https://regex101.com/r/niNjwp/1
"""

    return msg

================================
🪂 Subset with ``searchString``
================================

Subsetting is done using the GRIB2 index files. Index files define the grib variables/parameters of each message (sometimes it is useful to think of a grib message as a "layer" of the file) and define the byte range of the message.

Herbie can subset a file by grib message by downloading a byte range of the file. This way, instead of downloading the full file, you can download just the "layer" of the file you want. The searchString method implemented in Herbie to do a partial download is similar to what is explained here: https://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html


Herbie supports reading two different types of index files

1. Index files output by the **wgrib2** command-line utility. These index files are common for forecast models provided by **NCEP**.
2. Index files output by the **grib_ls** command-line utlity. These index files are common for forecast models provided by **ECMWF**.

You can use regular expression to search for lines in the index file. If ``H`` is a Herbie object, the regex search is performed on the ``H.read_idx().search_this`` column of the DataFrame


If you need help with regular expression, search the web or look at this `cheatsheet <https://www.petefreitag.com/cheatsheets/regex/>`_. Check regular expressions with `regexr <https://regexr.com/>`_ or `regex101 <https://regex101.com/>`_.


wgrib2-style index files
------------------------
Here are some examples you can use for the ``searchString`` argument for the **wgrib2**-style index files.

================================= ========================================================
``searchString=``                 GRIB messages that will be downloaded
================================= ========================================================
``":TMP:2 m"``                    Temperature at 2 m.
``":TMP:"``                       Temperature fields at all levels.
``":UGRD:.* mb"``                 U Wind at all pressure levels.
``":500 mb:"``                    All variables on the 500 mb level.
``":APCP:"``                      All accumulated precipitation fields.
``":APCP:surface:0-[1-9]*"``      Accumulated precip since initialization time
``":APCP:surface:[1-9]*-[1-9]*"`` Accumulated precip over last hour
``":UGRD:10 m"``                  U wind component at 10 meters.
``":(U|V)GRD:(10|80) m"``         U and V wind component at 10 and 80 m.
``":(U|V)GRD:"``                  U and V wind component at all levels.
``":.GRD:"``                      (Same as above)
``":(TMP|DPT):"``                 Temperature and Dew Point for all levels .
``":(TMP|DPT|RH):"``              TMP, DPT, and Relative Humidity for all levels.
``":REFC:"``                      Composite Reflectivity
``":surface:"``                   All variables at the surface.
``"^TMP:2 m.*fcst$"``             Beginning of string (^), end of string ($) wildcard (.*)
================================= ========================================================


ecCodes-style index files
-------------------------

Here are some examples you can use for the ``searchString`` argument for the **grib_ls**-style index files.

Look at the ECMWF GRIB Parameter Database
https://apps.ecmwf.int/codes/grib/param-db

This table is for the operational forecast product (and ensemble product):

======================== ==============================================
searchString (oper/enso) Messages that will be downloaded
======================== ==============================================
":2t:"                   2-m temperature
":10u:"                  10-m u wind vector
":10v:"                  10-m v wind vector
":10(u|v):               **10m u and 10m v wind**
":d:"                    Divergence (all levels)
":gh:"                   geopotential height (all levels)
":gh:500"                geopotential height only at 500 hPa
":st:"                   soil temperature
":tp:"                   total precipitation
":msl:"                  mean sea level pressure
":q:"                    Specific Humidity
":r:"                    relative humidity
":ro:"                   Runn-off
":skt:"                  skin temperature
":sp:"                   surface pressure
":t:"                    temperature
":tcwv:"                 Total column vertically integrated water vapor
":vo:"                   Relative vorticity
":v:"                    v wind vector
":u:"                    u wind vector
":(t|u|v|r):"            Temp, u/v wind, RH (all levels)
":500:"                  All variables on the 500 hPa level
======================== ==============================================

This table is for the wave product (and ensemble wave product):

======================== ==============================================
searchString (wave/waef) Messages that will be downloaded
======================== ==============================================
":swh:"                  Significant height of wind waves + swell
":mwp:"                  Mean wave period
":mwd:"                  Mean wave direction
":pp1d:"                 Peak wave period
":mp2:"                  Mean zero-crossing wave period
======================== ==============================================

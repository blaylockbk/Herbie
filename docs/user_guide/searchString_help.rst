.. hint::

    Use regular expression to search for lines in the .idx file
    Here are some examples you can use for ``searchString``
    ================================= ===============================================
    ``searchString``                  GRIB messages that will be downloaded
    ================================= ===============================================
    ``':TMP:2 m'``                    Temperature at 2 m.
    ``':TMP:'``                       Temperature fields at all levels.
    ``':UGRD:.* mb'``                 U Wind at all pressure levels.
    ``':500 mb:'``                    All variables on the 500 mb level.
    ``':APCP:'``                      All accumulated precipitation fields.
    ``':APCP:surface:0-[1-9]*'``      Accumulated precip since initialization time
    ``':APCP:surface:[1-9]*-[1-9]*'`` Accumulated precip over last hour
    ``':UGRD:10 m'``                  U wind component at 10 meters.
    ``':(U|V)GRD:(10|80) m'``         U and V wind component at 10 and 80 m.
    ``':(U|V)GRD:'``                  U and V wind component at all levels.
    ``':.GRD:'``                      (Same as above)
    ``':(TMP|DPT):'``                 Temperature and Dew Point for all levels .
    ``':(TMP|DPT|RH):'``              TMP, DPT, and Relative Humidity for all levels.
    ``':REFC:'``                      Composite Reflectivity
    ``':surface:'``                   All variables at the surface.
    ================================= ===============================================
    If you need help with regular expression, search the web
    or look at this cheatsheet: https://www.petefreitag.com/cheatsheets/regex/
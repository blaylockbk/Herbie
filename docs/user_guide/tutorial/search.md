# 🪂 Subset with `searchString`

Message subsetting is done using the GRIB2 index files. Index files define the grib variables/parameters of each message (sometimes it is useful to think of a grib message as a "layer" of the file) and define the byte range of the message.

Herbie can subset a file by grib message by downloading a byte range of the file. This way, instead of downloading the full file, you can download just the "layer" of the file you want. The searchString method implemented in Herbie to do a partial download is similar to what is explained in the [wgrib2 docs](https://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html).

Herbie supports reading two different types of index files

1. Index files output by the **wgrib2** command-line utility. These index files are common for forecast models provided by **NCEP**.
2. Index files output by the **ecCodes/grib_ls** command-line utility. These index files are common for forecast models provided by **ECMWF**.

You can use regular expression to search for lines in the index file. If `H` is a Herbie object, the regex search is performed on the `H.inventory().search_this` column of the DataFrame

> 🔥 **Tip:** If you need help with regular expression, search the web or look at this [cheatsheet](https://www.petefreitag.com/cheatsheets/regex/). Check regular expressions with [regexr](https://regexr.com/), [regex101](https://regex101.com/) or [cyrilex](https://extendsclass.com/regex-tester.html).

## wgrib2-style index files

Here are some examples you can use for the `searchString` argument for the **wgrib2**-style index files.

| `searchString=`                         | GRIB messages that will be downloaded                     |
| --------------------------------------- | --------------------------------------------------------- |
| `":TMP:2 m"`                            | Temperature at 2 m.                                       |
| `":TMP:"`                               | Temperature fields at all levels.                         |
| `":UGRD:\d+ mb"`                        | U Wind at all pressure levels.                            |
| `":500 mb:"`                            | All variables on the 500 mb level.                        |
| `":APCP:"`                              | All accumulated precipitation fields.                     |
| `":APCP:surface:0-[1-9]*"`              | Accumulated precip since initialization time              |
| `":APCP:.*:(?:0-1\|[1-9]\d*-\d+) hour"` | Accumulated precip over last hour                         |
| `":UGRD:10 m"`                          | U wind component at 10 meters.                            |
| `":[U\|V]GRD:[1,8]0 m"`                 | U and V wind component at 10 and 80 m.                    |
| `":[U\|V]GRD:"`                         | U and V wind component at all levels.                     |
| `":.GRD:"`                              | (Same as above)                                           |
| `":[U\|V]GRD:\d+ hybrid"`               | U and V wind components at all hybrid levels              |
| `":[U\|V]GRD:\d+ mb"`                   | U and V wind components at all pressure levels            |
| `":(?:TMP\|DPT):"`                      | Temperature and Dew Point for all levels .                |
| `":(?:TMP\|DPT\|RH):"`                  | TMP, DPT, and Relative Humidity for all levels.           |
| `":REFC:"`                              | Composite Reflectivity                                    |
| `":surface:"`                           | All variables at the surface.                             |
| `"^TMP:2 m.*fcst$"`                     | Beginning of string (^), end of string ($) wildcard (.\*) |

> 🔥 **Hint:** The NCEP [Parameters & Units Table 2](https://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html) and [GRIB2 Code Table 4.2](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-2.shtml) are useful resources to help you identify wgrib2-style GRIB variable abbreviations and their meanings.

If you can't figure out the right search string, you may also _Brute Force_ the search string for complex rules.

```python
searchString = "(string1|string2|string3|string4|string5|string6)"
```

For example, here is another way to get 1-hr precipiation variables using the brute force approach

```python
match_these = [f":APCP:surface:{i}-{i+1} h*" for i in range(47)]
searchString = f"({'|'.join(match_these)})"
```

will produce a long string with many regex groups:

```python
"(:APCP:surface:0-1 h*|:APCP:surface:1-2 h*|:APCP:surface:2-3 h*|:APCP:surface:3-4 h*|:APCP:surface:4-5 h*|:APCP:surface:5-6 h*|:APCP:surface:6-7 h*|:APCP:surface:7-8 h*|:APCP:surface:8-9 h*|:APCP:surface:9-10 h*|:APCP:surface:10-11 h*|:APCP:surface:11-12 h*|:APCP:surface:12-13 h*|:APCP:surface:13-14 h*|:APCP:surface:14-15 h*|:APCP:surface:15-16 h*|:APCP:surface:16-17 h*|:APCP:surface:17-18 h*|:APCP:surface:18-19 h*|:APCP:surface:19-20 h*|:APCP:surface:20-21 h*|:APCP:surface:21-22 h*|:APCP:surface:22-23 h*|:APCP:surface:23-24 h*|:APCP:surface:24-25 h*|:APCP:surface:25-26 h*|:APCP:surface:26-27 h*|:APCP:surface:27-28 h*|:APCP:surface:28-29 h*|:APCP:surface:29-30 h*|:APCP:surface:30-31 h*|:APCP:surface:31-32 h*|:APCP:surface:32-33 h*|:APCP:surface:33-34 h*|:APCP:surface:34-35 h*|:APCP:surface:35-36 h*|:APCP:surface:36-37 h*|:APCP:surface:37-38 h*|:APCP:surface:38-39 h*|:APCP:surface:39-40 h*|:APCP:surface:40-41 h*|:APCP:surface:41-42 h*|:APCP:surface:42-43 h*|:APCP:surface:43-44 h*|:APCP:surface:44-45 h*|:APCP:surface:45-46 h*|:APCP:surface:46-47 h*)"
```

## ecCodes-style index files

Here are some examples you can use for the `searchString` argument for the **grib_ls**-style index files.

Look at the [ECMWF GRIB Parameter Database](https://apps.ecmwf.int/codes/grib/param-db)

This table is for the operational forecast product (and ensemble product):

| `searchString`     | (oper/enso) Messages that will be downloaded   |
| ------------------ | ---------------------------------------------- |
|                    |                                                |
| `":2t:"`           | 2-m temperature                                |
| `":10u:"`          | 10-m u wind vector                             |
| `":10v:"`          | 10-m v wind vector                             |
| `":10(u\|v):`      | **10m u and 10m v wind**                       |
| `":d:"`            | Divergence (all levels)                        |
| `":gh:"`           | geopotential height (all levels)               |
| `":gh:500`         | geopotential height only at 500 hPa            |
| `":st:"`           | soil temperature                               |
| `":tp:"`           | total precipitation                            |
| `":msl:"`          | mean sea level pressure                        |
| `":q:"`            | Specific Humidity                              |
| `":r:"`            | relative humidity                              |
| `":ro:"`           | Runn-off                                       |
| `":skt:"`          | skin temperature                               |
| `":sp:"`           | surface pressure                               |
| `":t:"`            | temperature                                    |
| `":tcwv:"`         | Total column vertically integrated water vapor |
| `":vo:"`           | Relative vorticity                             |
| `":v:"`            | v wind vector                                  |
| `":u:"`            | u wind vector                                  |
| `":(t\|u\|v\|r):"` | Temp, u/v wind, RH (all levels)                |
| `":500:"`          | All variables on the 500 hPa level             |

This table is for the wave product (and ensemble wave product):

| `searchString` (wave/waef) | Messages that will be downloaded         |
| ------------------------ | ---------------------------------------- |
| `":swh:"`                | Significant height of wind waves + swell |
| `":mwp:"`                | Mean wave period                         |
| `":mwd:"`                | Mean wave direction                      |
| `":pp1d:"`               | Peak wave period                         |
| `":mp2:"`                | Mean zero-crossing wave period           |

> 🔥 **Hint:** The [ECMWF Parameter Database](https://apps.ecmwf.int/codes/grib/param-db?filter=grib2) is a useful resource to help you identify ecCodes-style GRIB variable abbreviations and their meanings.

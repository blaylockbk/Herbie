**Brian Blaylock**  

# How to download archived HRRR GRIB2 files
The High Resolution Rapid Refresh model output is archived by the MesoWest group at the University of Utah on the
CHPC Pando Archive System.

This repository demonstrates how to download HRRR files from the archive.

For more information, go to http://hrrr.chpc.utah.edu/

## Jupyter Notebooks
- [Part 1: How to download a bunch of HRRR grib2 files (full file)](./notebooks/demo_download_hrrr_archive_part1.ipynb)
- [Part 2: How to download a subset of variables from a HRRR file](./notebooks/demo_download_hrrr_archive_part2.ipynb)
- [Part 3: A function that can download many full files, or subset of files](./notebooks/demo_download_hrrr_archive_part3.ipynb)
- [Part 4: Opening GRIB2 files in Python with xarray and cfgrib](./notebooks/demo_download_hrrr_archive_part4.ipynb)

## Useful Functions in `HRRR_archive.py`
Feel free to use these functions and imporve upon them to fit your needs. If you wrote a function that is really cool and want to share it here, make a pull request.

- [`HRRR_archive.py`](./HRRR_archive.py)

To use these functions, copy this file to the path with your own python scripts and import them

    from HRRR_archive import *
    
Requires `xarray`, `cfgrib`, `cartopy`, `pandas`, `requests`, `urllib`

For reference, here are some useful values you can set `searchString` to download certain variables.


|`searchString=`| GRIB fields that will be downloaded
|--|--
|`':TMP:2 m'`      | Temperature at 2 m.
|`':TMP:'`         | Temperature fields at all levels.
|`':500 mb:'`      | All variables on the 500 mb level.
|`':APCP:'`        | All accumulated precipitation fields.
|`':UGRD:10 m:'`   | U wind component at 10 meters.
|`':(U\|V)GRD:'`    | U and V wind component at all levels.
|`':.GRD:'`        | (Same as above)
|`':(TMP\|DPT):'`   | Temperature and Dew Point for all levels .
|`':(TMP\|DPT\|RH):'`| TMP, DPT, and Relative Humidity for all levels.
|`':REFC:'`        | Composite Reflectivity
|`':surface:'`     | All variables at the surface.

⚠ The functions in `HRRR_archive.py` might be slightly different than those used in the demonstration Jupyter Notebooks. These are usually better changes.


> **Note on precipitation field (APCP)**
>A lot of users have asked why the precipitation accumulation fields are all zero for the model analysis (F00). That is becuase it is an accumulation variable over a period of time. At the model analysis, there has been no precipitaiton because no time has passed.
> When looking at precipitation, consider looking at F01, which will be the precipitiation amount between F00 and F01.


---
---

🌐 HRRR Archive Website: http://hrrr.chpc.utah.edu/  
🚑 Support: atmos-mesowest@lists.utah.edu  
📧 Brian Blaylock: blaylockbk@gmail.com  
✒ Citation this details:
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

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
Feel free to use these functions and improve upon them to fit your needs. If you write a useful function, send me a `.py` file or make a pull request to share your script.

### [`HRRR_archive.py`](./HRRR_archive.py)

|Function| what it will do for you
|--|--
|`download_HRRR`| Downloads full or partial HRRR files for one or more datetimes and forecast hours.  
|`get_HRRR` | Downloads HRRR data for a single datetime/forecast and returns as an xarray Dataset or list of Datasets.

To use these functions, copy the `HRRR_archive.py` file to the directory path you are working in or include the path in your PYTHONPATH.

    from HRRR_archive import download_HRRR, get_HRRR
    
Requires `xarray`, `cfgrib`, `cartopy`, `pandas`, `requests`, `urllib`

**A note on the `searchString` argument:** These functions have an option to define a `searchString` that is used to specify variables you want to download. For example, instead of downloading the full HRRR file, you could download just the wind or precipitation variables. Read the docstring for the functions or look at [notebook #2](./notebooks/demo_download_hrrr_archive_part2.ipynb) for more details. For reference, here are some useful examples to give you some ideas...


|`searchString=`| GRIB fields that will be downloaded
|--|--
|`':TMP:2 m'`      | Temperature at 2 m
|`':TMP:'`         | Temperature fields at all levels
|`':500 mb:'`      | All variables on the 500 mb level
|`':APCP:'`        | All accumulated precipitation fields
|`':UGRD:10 m'`   | U wind component at 10 meters
|`':(U\|V)GRD:'`    | U and V wind component at all levels
|`':.GRD:'`        | (Same as above)
|`'(WIND\|GUST\|UGRD\|VGRD):(surface\|10 m)`| Surface wind, surface gusts, and 10 m u- v-components
|`':(TMP\|DPT):'`   | Temperature and Dew Point for all levels
|`':(TMP\|DPT\|RH):'`| TMP, DPT, and Relative Humidity for all levels
|`':REFC:'`        | Composite Reflectivity
|`:(APCP\|REFC):`| Precipitation and reflectivity
|`':surface:'`     | All variables at the surface

⚠ The functions in `HRRR_archive.py` might be slightly different than those used in the demonstration Jupyter Notebooks. These differences should be for the better.

> **Note on precipitation fields (e.g., APCP)**
>A lot of users have asked why the precipitation accumulation fields are all zero for the model analysis (F00). That is because it is an accumulation variable over a period of time. At the model analysis, there has been no precipitation because no time has passed.
> When looking at precipitation, consider looking at F01, which will be the precipitation amount between F00 and F01.

## 🐍  Anaconda Environment
I provide an `environment.yml` with all the packages you should install. If this is new to you, I suggest you become be familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

    conda env create -f environment.yml

Then activate the environment

    conda activate hrrr_archive

---
---

🌐 HRRR Archive Website: http://hrrr.chpc.utah.edu/  
🚑 Support: atmos-mesowest@lists.utah.edu  
📧 Brian Blaylock: blaylockbk@gmail.com  
✒ Citation this details:
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

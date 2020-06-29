**Brian Blaylock**  

# How to download archived HRRR GRIB2 files
The High Resolution Rapid Refresh model output is archived by the MesoWest group at the University of Utah on the
CHPC Pando Archive System. This repository demonstrates how to download HRRR files from the archive with Python.

|HRRR Archive Webpage|
|:--:|
|**http://hrrr.chpc.utah.edu/**|

---

## 🐍  Conda Environment
These examples use Python 3. The `environment.yml` file lists all the packages you will need. If you have [Anaconda](https://www.anaconda.com/products/individual) installed, create this envrionment with 

    conda env create -f environment.yml

Then activate the `hrrr_archive` environment with

    conda activate hrrr_archive

If conda environments are new to you, I suggest you become familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

---

## 📝 Detailed Jupyter Notebooks
In these notebooks, I give a bit of discussion on how I download HRRR files from Pando.
- [Part 1: How to download a bunch of HRRR grib2 files (full file)](./notebooks/demo_download_hrrr_archive_part1.ipynb)
- [Part 2: How to download a subset of variables from a HRRR file](./notebooks/demo_download_hrrr_archive_part2.ipynb)
- [Part 3: A function that can download many full files, or subset of files](./notebooks/demo_download_hrrr_archive_part3.ipynb)
- [Part 4: Opening GRIB2 files in Python with xarray and cfgrib](./notebooks/demo_download_hrrr_archive_part4.ipynb)
- [Examples that import `HRRR_archive.py`](./notebooks/examples.ipynb)

---

## 👨🏻‍💻 `HRRR_archive.py` -- All the useful functions in one module 
If you are looking for a no-fuss method to download the HRRR data you want, use the `HRRR_archive.py` module. Feel free to edit/improve it to fit your needs. If you write a useful function, send me a `.py` file or make a pull request to share your script.

> Requires `xarray`, `cfgrib`, `cartopy`, `requests`

### [`HRRR_archive.py`](./HRRR_archive.py)

|Function| what it will do for you
|--|--
|`download_HRRR`| Downloads full or partial HRRR files for one or more datetimes and forecast hours.
|`get_HRRR` | Downloads HRRR data for a single datetime/forecast and returns as an xarray Dataset or list of Datasets.

⚠ The functions in `HRRR_archive.py` are different than (and better than) those used in the demonstration Jupyter Notebooks.

## [👉 Click Here For Some Examples](./notebooks/examples.ipynb)

***How do I import these functions?*** That depends on where you put the module and where the script is you are running. If `HRRR_archive.py` is in your current working directory or if it is in a directory included in your [PYTHONPATH](https://www.tutorialspoint.com/What-is-PYTHONPATH-environment-variable-in-Python), then simply import the functions with

    from HRRR_archive import download_HRRR, get_HRRR

If you put `HRRR_archive.py` in a different directory, you will need to tell your Python script where to find it. You can do that by appending the `sys.path`.

    import sys
    sys.path.append('/directory/location/of/the/HRRR_achive/module/')

    from HRRR_archive import download_HRRR, get_HRRR

***A note on the `searchString` argument:*** One of the function's arguments is `searchString` which is used to specify variables you want to download. For example, instead of downloading the full GRIB2 file, you could download just the wind or precipitation variables. Read the docstring for the functions or look at [notebook #2](./notebooks/demo_download_hrrr_archive_part2.ipynb) for more details. 

For reference, here are some useful examples to give you some ideas...

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
|`'((U\|V)GRD:10 m\|TMP:2 m\|APCP)'` | 10-m wind, 2-m temp, and precip.

> **Note on precipitation fields (e.g., APCP)**
>A lot of users have asked why the precipitation accumulation fields are all zero for the model analysis (F00). That is because it is an *accumulation* variable over a period of time. At the model analysis time, there has been no precipitation because no time has passed.
>
>- **F00** only has a 0-0 hour accumulation (always zero)
>- **F01** only has a 0-1 hour accumulation
>- **F02** has a 0-2 hour accumulation and a 1-2 hour accumulation.
>- **F03** has a 0-3 hour accumulation and a 2-3 hour accumulation.
>- etc.

<br>

**Best of luck 🍀**  
\- Brian

---

🌐 HRRR Archive Website: http://hrrr.chpc.utah.edu/  
🚑 Support: atmos-mesowest@lists.utah.edu  
📧 Brian Blaylock: blaylockbk@gmail.com  
✒ Citation this details:
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

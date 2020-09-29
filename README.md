|![](https://raw.githubusercontent.com/blaylockbk/SynopticPy/master/images/Balloon_logo/balloon_bkb_sm.png)|**Brian Blaylock**<br>🌐 [Webpage](http://home.chpc.utah.edu/~u0553130/Brian_Blaylock/home.html)
|:--|:--|


# Brian's High-Resolution Rapid Refresh code: HRRR-B

|HRRR Archive Website|**http://hrrr.chpc.utah.edu/**|
|--:|:--|

**HRRR-B**, or "Herbie," is a python package for downloading recent and archived High Resolution Rapid Refresh (HRRR) model forecasts. I created a lot of this during my PhD and decided to organize what I had into a more coherent package. It will continue to evolve at my leisure.

HRRR model output is archived by the MesoWest group at the University of Utah on the [CHPC Pando Archive System](http://hrrr.chpc.utah.edu/). The GRIB2 files are copied from from NCEP every couple hours. Google also has a growing HRRR archive. Between these three data sources, there is a lot of archived HRRR data available.

This package demonstrates how to download those HRRR files with Python.

- Download full or partial HRRR GRIB2 files. Partial files are downloaded by GRIB message.
- Three different data sources: [NCEP-NOMADS](https://nomads.ncep.noaa.gov/), [Pando (University of Utah)](http://hrrr.chpc.utah.edu/), and [Google Cloud](https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh?pli=1). 
    - > The Pando HRRR archive is in [process of moving to Amazon Web Services](https://github.com/blaylockbk/HRRR_archive_download/issues/2) as a public [Earth](https://aws.amazon.com/earth/) dataset. It will be available in [zarr](https://zarr.readthedocs.io/en/stable/) format that will allow for more flexibility for chunked data requests.
- Open HRRR data as an xarray.Dataset.
- Other useful tools (in development), like indexing nearest neighbor points and getting a cartopy crs object.

> ## Goals
> This package is still being developed. I want to make it so you can do this:
> ```python
> import hrrrb.archive as ha
> ```
> or
> ``` python
> from hrrrb.archive import get_hrrr
> ```
> And I want to publish this on PyPI.

<img src='https://raw.githubusercontent.com/blaylockbk/HRRR_archive_download/master/images/Herbie3.png' width=350 style='float:right;margin:10px' align=right>

## 🌹 What's in a name? 
How do you pick the right name? For now, I settled on the name **HRRR-B**, pronounced "Herbie," because this package helps you get data from the High-Resolution Rapid Refresh (HRRR) model, and the B is for Brian. Is it a little pretentious to attach your own name to a package? Maybe the B stands for something else someday. I'm also thinking about just naming this "Herbie" and you would import with `import herbie.archive as ha`

## Contributing Guidelines (and disclaimer)
The intent of this package is to serve as an _example_ of how you can download HRRR data from the Pando HRRR archive. Since this package is a work in progress, it is distributed "as is." I do not make any guarantee it will work for you out of the box. Any revisions I make are purely for my benefit. Sorry if I break something, but I usually only push updates to GitHub if the code is in a reasonably functional state (at least, in the way I use it).

With that said, I am happy to share this project with you. You are welcome to open issues and submit pull requests, but know that I may or may not get around to doing anything about it. If this is helpful to you in any way, I'm glad.

---

## 🐍  Conda Environment
These examples use Python 3. The `environment.yml` file lists all the packages you will need, plus a few useful extras. If you have [Anaconda](https://www.anaconda.com/products/individual) installed, create this envrionment with 

    conda env create -f environment.yml

Then activate the `hrrrb` environment with

    conda activate hrrrb

If conda environments are new to you, I suggest you become familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

---

## 📝 Detailed Jupyter Notebooks

These notebooks show practical use case of the `hrrrb` package:
- [Package Examples](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/examples.ipynb)

These notebooks offer a bit of discussion on how the download package works. They aren't as practical, (and have probably changed a little), but helps illustrate the download method.
- [Part 1: How to download a bunch of HRRR grib2 files (full file)](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part1.ipynb)
- [Part 2: How to download a subset of variables from a HRRR file](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part2.ipynb)
- [Part 3: A function that can download many full files, or subset of files](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part3.ipynb)
- [Part 4: Opening GRIB2 files in Python with xarray and cfgrib](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part4.ipynb)

⚠ The functions in `hrrrb.archive` slightly different than (and better than) these discussion notebooks.

---

## 👨🏻‍💻 `hrrrb.archive` -- All the useful functions in one module 
If you are looking for a no-fuss method to download the HRRR data you want, use the `hrrrb.archive` module. Feel free to edit/improve it to fit your needs. If you write a useful function, send me a `.py` file or make a pull request to share your script.

> Requires `xarray`, `cfgrib`, `cartopy`, `requests`

|Function| what it will do for you
|--|--
|`download_hrrr`| Downloads full or partial HRRR files for one or more datetimes and forecast hours.
|`get_hrrr` | Downloads HRRR data for a single datetime/forecast and returns as an xarray Dataset or list of Datasets.


## [👉 Click Here For Some Examples](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/examples.ipynb)

***How do I import these functions?*** That depends on where you put the module and where the script you are running is located. 

Install via PyPiI(coming soon)

```bash
pip install hrrrb
```
If `hrrrb` is in your current working directory or if it is in a directory included in your [PYTHONPATH](https://www.tutorialspoint.com/What-is-PYTHONPATH-environment-variable-in-Python), then simply import the functions with
```python
from hrrrb.archive import download_hrrr, get_hrrr
```

If `hrrrb` is in a different directory, you will need to tell your Python script where to find it. You can do that by appending the `sys.path` in your script.
```python
import sys
sys.path.append('/directory/location/of/hrrrb')

from hrrrb.archive import download_hrrr, get_hrrr
```
## Function arguments

```python
download_hrrr(DATES, searchString=None, fxx=range(0, 1), *,
              model='hrrr', field='sfc',
              download_dir='./', dryrun=False, verbose=True)

get_hrrr(DATE, searchString, *, fxx=0, DATE_is_valid_time=False, 
         remove_grib2=True, add_crs=True, **download_kwargs):
```

- `DATES` Datetime or list of datetimes representing the model initialization time.
- `searchString` **See note below**
- `fxx` Range or list of forecast hours.
    - e.g., `range(0,19)` for F00-F18
    - Default is the model analysis (F00).
- `model` The type of model. 
    - Options are `hrrr`, `alaska`, `hrrrX`
- `field` The type of field file. 
    - Options are `sfc` and `prs`
    - `nat` and `subh` are only available for today and yesterday.
- `download_dir` The directory path the files will be saved in. 
    - Default downloads files into the user's home directory `~/data/hrrr`.
- `dryrun` If `True`, the function will tell you what it will download but not actually download anything.
- `verbose` If `True`, prints lots of info to the screen.

Specific to `get_hrrr`:
- `DATE_is_valid_time` For *get_hrrr*, if `True` the input DATE will represent the valid time. If `False`, DATE represents the the model run time.
- `remove_grib2` For *get_hrrr*, the grib2 file downloaded will be removed after reading the data into an xarray Dataset.
- `add_crs` For *get_hrrr*, will create a cartopy coordinate reference system object and append it as a Dataset attribute.


## The important `searchString` argument
`searchString` is used to specify select variables you want to download. For example, instead of downloading the full GRIB2 file, you could download just the wind or precipitation variables. Read the docstring for the functions or look at [notebook #2](./notebooks/demo_download_hrrr_archive_part2.ipynb) for more details. 

`searchString` uses regular expression to search for GRIB message lines in the files .idx file. There must be a .idx file for the GRIB2 file for the search to work. 

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
|`'((U\|V)GRD:10 m\|TMP:2 m\|APCP)'` | 10-m wind, 2-m temp, and accumulated precipitation.

<br><br>

> **Are you working with precipitation fields? (e.g., APCP)**  
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


Thanks for using HRRR-B
![](https://raw.githubusercontent.com/blaylockbk/HRRR_archive_download/master/images/herbie.jpg)
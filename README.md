# 📔 [Documentation Page](https://blaylockbk.github.io/HRRR_archive_download/_build/html/)

|![](https://raw.githubusercontent.com/blaylockbk/SynopticPy/master/images/Balloon_logo/balloon_bkb_sm.png)|**Brian Blaylock**<br>🌐 [Webpage](http://home.chpc.utah.edu/~u0553130/Brian_Blaylock/home.html)<br>[🔩 PyPI](https://pypi.org/user/blaylockbk/)
|:--|:--|


# Brian's High-Resolution Rapid Refresh tools: HRRR-B

<!-- Badges -->
[![](https://img.shields.io/pypi/v/hrrrb)](https://pypi.python.org/pypi/hrrrb/)
![](https://img.shields.io/github/license/blaylockbk/HRRR_archive_download)
[![DOI](https://zenodo.org/badge/275214142.svg)](https://zenodo.org/badge/latestdoi/275214142)

|HRRR Archive Website|**http://hrrr.chpc.utah.edu/**|
|--:|:--|

**HRRR-B**, or "Herbie," is a python package for downloading recent and archived High Resolution Rapid Refresh (HRRR) model forecasts and opening HRRR data in an xarray.Dataset. I created most of this during my PhD and decided to organize what I created into a more coherent package. It will continue to evolve at my own leisure.

## About `HRRR-B`
HRRR model output is archived by the MesoWest group at the University of Utah on the [CHPC Pando Archive System](http://hrrr.chpc.utah.edu/). The GRIB2 files are copied from from NCEP every couple hours. NOAA started pushing HRRR data to Google and AWS at in the later half of 2020. Between these data sources, there is a lot of archived HRRR data available. **This Python package helps download those archived HRRR files.**

- Download full or partial HRRR GRIB2 files. Partial files are downloaded by GRIB message.
- Different data sources: [NCEP-NOMADS](https://nomads.ncep.noaa.gov/), [Pando (University of Utah)](http://hrrr.chpc.utah.edu/), [Google Cloud Platform](https://console.cloud.google.com/storage/browser/high-resolution-rapid-refresh?pli=1), and [Amazon Web Services](). 
    - > The Pando HRRR archive is in [process of moving to Amazon Web Services](https://github.com/blaylockbk/HRRR_archive_download/issues/2) as a public [Earth](https://aws.amazon.com/earth/) dataset. It will be available in [zarr](https://zarr.readthedocs.io/en/stable/) format that will allow for more flexibility for chunked data requests. See [Issue #2](https://github.com/blaylockbk/HRRR_archive_download/issues/2).
- Open HRRR data as an xarray.Dataset.
- Other useful tools (in development), like indexing nearest neighbor points and getting a cartopy crs object.

<img src='https://raw.githubusercontent.com/blaylockbk/HRRR_archive_download/master/images/Herbie3.png' width=350 style='float:right;margin:10px' align=right>

## 🌹 What's in a name? 
How do you pick the right name? For now, I settled on the name **HRRR-B**, pronounced "Herbie," because this package helps you get data from the High-Resolution Rapid Refresh (HRRR) model, and the B is for Brian. Is it a little pretentious to attach your own name to a package? Maybe the B will stand for something else someday. I'm also thinking about just naming this "Herbie," but that name is already taken on PyPI.

## Contributing Guidelines (and disclaimer)
The intent of this package is to serve as an _example_ of how you can download HRRR data from the Pando HRRR archive, but it might be useful for you. Since this package is a work in progress, it is distributed "as is." I do not make any guarantee it will work for you out of the box. Any revisions I make are purely for my benefit. Sorry if I break something, but I usually only push updates to GitHub if the code is in a reasonably functional state (at least, in the way I use it).

With that said, I am happy to share this project with you. You are welcome to open issues and submit pull requests, but know that I may or may not get around to doing anything about it. If this is helpful to you in any way, I'm glad.

> ## What if I don't like this package?
> As an alternative you can use [rclone](https://rclone.org/) to download HRRR files from AWS or GCP. I quite like rclone. Here is a [short rclone tutorial](https://github.com/blaylockbk/pyBKB_v3/blob/master/rclone_howto.md)
 
---

# 🐍 Installation and Conda Environment
This package requires **Python 3.7+** (doesn't work in 3.6 and earlier because I use relative imports)

### Option 1: pip
Install the last published version from PyPI.

```bash
pip install hrrrb
```

But the version on PyPI has diverged a lot from the code on GitHub, so I would recommend not getting from PyPI. To get the most recent hrrrb code, you may install the package directly from GitHub

```bash
pip install git+https://github.com/blaylockbk/HRRR_archive_download.git
```

> Requires: xarray, cfgrib, pandas, cartopy, requests, curl  
> Optional: matplotlib, cartopy

### Option 2: conda
If conda environments are new to you, I suggest you become familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

I have provided a sample Anaconda [environment.yml](https://github.com/blaylockbk/HRRR_archive_download/blob/master/environment.yml) file that lists the minimum packages required plus some extras that might be useful when working with other types of weather data. Look at the bottom lines of that yaml file...there are two ways to install `hrrrb` with pip. Comment out the lines you don't want.

For the latest development code:
```yaml
- pip:
    - git+https://github.com/blaylockbk/HRRR_archive_download.git
```
For the latest published version
```yaml
- pip:
    - hrrrb
```

First, create the virtual environment with 

```bash
conda env create -f environment.yml
```

Then, activate the `hrrrb` environment. Don't confuse this _environment_ name with the _package_ name.

```bash
conda activate hrrrb
```

Occasionally, you might want to update all the packages in the environment.

```bash
conda env update -f environment.yml
```

> ### Alternative "Install" Method
> There are several other ways to "install" a python package so you can import them. One alternatively is you can `git clone https://github.com/blaylockbk/HRRR_archive_download.git` this repository to any directory. To import the package, you will need to update your PYTHONPATH environment variable to find the directory you put this package or add the line `sys.path.append("/path/to/hrrrb")` at the top of your python script.

---

# 📝 Jupyter Notebooks

These notebooks show practical use case of the `hrrrb` package:
- [Main Package Examples](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/examples.ipynb)

These notebooks offer a deeper discussion on how the download process works. These are not intended for practical use, but should help illustrate my thought process when I created this package.
- [Part 1: How to download a bunch of HRRR grib2 files (full file)](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part1.ipynb)
- [Part 2: How to download a subset of variables from a HRRR file](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part2.ipynb)
- [Part 3: A function that can download many full files, or subset of files](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part3.ipynb)
- [Part 4: Opening GRIB2 files in Python with xarray and cfgrib](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part4.ipynb)

These are additional notebooks for useful tips/tricks
- [How to make Cartopy maps with HRRR data with Brian's `common_features` helper](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_plot-on-map-with-common-features.ipynb)
---

# 👨🏻‍💻 `hrrrb.archive`
If you are looking for a no-fuss method to download the HRRR data you want, use the `hrrrb.archive` module.

```python
import hrrrb.archive as ha
```
or
``` python
from hrrrb.archive import download_hrrr, xhrrr
```

|Main Functions| What it will do for you...
|--|--
|`download_hrrr`| Downloads full or partial HRRR GRIB2 files to local disk.
|`xhrrr` | Downloads single HRRR file and returns as an `xarray.Dataset` or list of Datasets.


## [👉 Click Here For Some Examples](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/examples.ipynb)

## Function arguments

```python
# Download full GRIB2 files to local disk
download_hrrr(DATES, searchString=None, *, 
              fxx=range(0, 1),
              model='hrrr',
              field='sfc',
              save_dir=_default_save_dir,
              download_source_priority=None,
              dryrun=False, verbose=True)
```
```python
# Download file and open as xarray
xhrrr(DATE, searchString, fxx=0, *,
      DATE_is_valid_time=False,
      remove_grib2=True,
      add_crs=True,
      **download_kwargs)
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
- `save_dir` The directory path the files will be saved in. 
    - By default, GRIB2 files are downloaded into the user's home directory at `~/data/{model}`. The default directory can be changed in the `~/.config/hrrrb/config.cfg` file. This file is generated the first time you import **hrrrb.archive**.
- `download_source_priority` The default source priority is `['pando', 'google', 'nomads']`, but you might want to instead try to download a file from Google before trying to get it from Pando. In that case, set to `['google', 'pando', 'nomads']`. 
- `dryrun` If `True`, the function will tell you what it will download but not actually download anything.
- `verbose` If `True`, prints lots of info to the screen.

Specific to `xhrrr`:
- `DATE_is_valid_time` For *xhrrr*, if `True` the input DATE will represent the valid time. If `False`, DATE represents the the model run time.
- `remove_grib2` For *xhrrr*, the grib2 file downloaded will be removed after reading the data into an xarray Dataset.
- `add_crs` For *xhrrr*, will create a cartopy coordinate reference system object and append it as a Dataset attribute.


## The **`searchString`** argument
`searchString` is used to specify select variables you want to download. For example, instead of downloading the full GRIB2 file, you could download just the wind or precipitation variables. Read the docstring for the functions or look at [notebook #2](./notebooks/demo_download_hrrr_archive_part2.ipynb) for more details. 

`searchString` uses regular expression to search for GRIB message lines in the files .idx file. There must be a .idx file for the GRIB2 file for the search to work. 

For reference, here are some useful examples to give you some ideas...

|`searchString=`| GRIB fields that will be downloaded
|--|--
|`':TMP:2 m'`      | Temperature at 2 m
|`':TMP:'`         | Temperature fields at all levels
|``':UGRD:.* mb'`` | U Wind at all pressure levels.
|`':500 mb:'`      | All variables on the 500 mb level
|`':APCP:'`        | All accumulated precipitation fields
|`':APCP:surface:0-[1-9]*'` | Accumulated since initialization time
|`':APCP:surface:[1-9]*-[1-9]*'`| Accumulated over last hour
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
>
> NOTE: When cfgrib reads a grib file with more than one accumulated precipitation fields, it will not read all the fields. I think this is an issue with cfgrib (see [issue here](https://github.com/ecmwf/cfgrib/issues/187)). The way around this is to key in on a *single* APCP field. See the `searchString` examples above for keying in on a single APCP field.
<br>

### Quickly look at GRIB files in the command line
There are two tools for looking at GRIB file contents in the command line.
1. `wgrib2` : can be installed via conda-forge in your environment. A product from NOAA.
2. `grib_ls` : is a dependency of cfgrib and is included when you install cfgrib in your environment. A product from ECMWF. 

For the sample precipitation data, below is the output using both tools

```bash
$ wgrib2 subset_20201214_hrrr.t00z.wrfsfcf12.grib2
1:0:d=2020121400:APCP:surface:0-12 hour acc fcst:
2:887244:d=2020121400:APCP:surface:11-12 hour acc fcst:
```

```bash
$ grib_ls subset_20201214_hrrr.t00z.wrfsfcf12.grib2 
subset_20201214_hrrr.t00z.wrfsfcf12.grib2
edition      centre       date         dataType     gridType     typeOfLevel  level        stepRange    shortName    packingType  
2            kwbc         20201214     fc           lambert      surface      0            0-12         tp           grid_complex_spatial_differencing 
2            kwbc         20201214     fc           lambert      surface      0            11-12        tp           grid_complex_spatial_differencing 
2 of 2 messages in subset_20201214_hrrr.t00z.wrfsfcf12.grib2

2 of 2 total messages in 1 files
```

I hope some of these tips are helpful to you.

**Best of luck 🍀**  
\- Brian

---

🌐 HRRR Archive Website: http://hrrr.chpc.utah.edu/  
🚑 Support: [GitHub Issues](https://github.com/blaylockbk/HRRR_archive_download/issues) or atmos-mesowest@lists.utah.edu  
📧 Brian Blaylock: blaylockbk@gmail.com  
✒ Pando HRRR Archive citation details:
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

Thanks for using HRRR-B
![](https://raw.githubusercontent.com/blaylockbk/HRRR_archive_download/master/images/herbie.jpg)

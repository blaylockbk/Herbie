
-----

# THIS IS THE OLD, DEPRECATED HRRR-B API

-----

# 👨🏻‍💻 Examples: Old `HRRR-B` API

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


## [👉 Click Here For Some Examples](https://github.com/blaylockbk/Herbie/blob/master/notebooks/examples.ipynb)

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
`searchString` is used to specify select variables you want to download. For example, instead of downloading the full GRIB2 file, you could download just the wind or precipitation variables. Read the docstring for the functions or look at [notebook #2](https://github.com/blaylockbk/Herbie/blob/master/notebooks/demo_download_hrrr_archive_part2.ipynb) for more details. 

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
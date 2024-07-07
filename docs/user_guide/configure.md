# 🛠 Configure

Herbie's default behavior is set in Herbie's configuration file:

```bash
~/.config/herbie/config.toml
```

This file is automatically created the first time you import Herbie. It is written in [TOML format](https://toml.io/en/). The default settings are

```toml
[default]
model = "hrrr"
fxx = 0
save_dir = "~/data"
overwrite = false
verbose = true
```

The configuration file is mostly a convenience. Any of the configured parameters can be overwritten when creating Herbie objects. For example, this will get the HRRR model and save data to the `~/data` directory, because those are the configured defaults:

```python
from herbie import Herbie
H = Herbie("2023-01-01")
```

But you can set the model and the save location when you create a Herbie object. The following sets a new model (GFS) and will save any downloaded content to the specified location:

```python
from herbie import Herbie
H = Herbie("2023-01-01", model="gfs", save_dir="/this/folder")
```

You might want to set change the default behavior by modifying the Herbie config file if you primarily work with a different model, want to save downloaded content to a different drive, need to use a different source priority, etc.

> If Herbie is unable to create its config file, then it will use the standard defaults.

## Change config file location

If you don't have write permissions in the default location, but you still want to use a config file, then you can set the environment variable `HERBIE_CONFIG_PATH` to specify a new path. **Changing the path to the config file is only advised if you don't have permission to write to the default location.**

```bash
export HERBIE_CONFIG_PATH="/my/path/herbie-config/
```

## Configurable settings

### `model`

Model name as defined in the [models](https://github.com/blaylockbk/Herbie/tree/main/herbie/models) template folder. CASE INSENSITIVE

Some examples:

- `'hrrr'` HRRR contiguous United States model
- `'hrrrak'` HRRR Alaska model (alias `'alaska'`)
- `'rap'` RAP model
- `'gfs'` Global Forecast System (atmosphere)
- `'gfs_wave'` Global Forecast System (wave)
- `'rrfs'` Rapid Refresh Forecast System prototype
- etc.

### `fxx`

Forecast lead time in hours. Available lead times depend on
the model type and model version. Range is model and run
dependent.

### `product`

Output variable product file type. If not specified, will
use first product in model template file. CASE SENSITIVE.

For example, the HRRR model has these products:

- `'sfc'` surface fields
- `'prs'` pressure fields
- `'nat'` native fields
- `'subh'` subhourly fields

### `member`

Some ensemble models (e.g., GEFS, RRFS) will need to specify an ensemble member number.

### `save_dir`

Location to save GRIB2 files locally. You may use system environment variables like `${HOME}`, and `${TMPDIR}`

This can overwrite the save directory by setting the environment variable `HERBIE_SAVE_DIR`

```bash
export HERBIE_SAVE_DIR="/my/new/save_dir/
```

### `overwrite`

- If `true`, look for GRIB2 file even if local copy exists.
- If `false`, use the local copy (still need to find the idx file on the remote server).

### `verbose`

- If `true`, print info to screen.
- If `false`, do not print extra info to screen.


### `priority`

List of data sources in the order of download priority. CASE INSENSITIVE. Available sources include

- `'aws'` Amazon Web Services (Big Data Program)
- `'nomads'` NOAA NOMADS server
- `'google'` Google Cloud Platform (Big Data Program)
- `'azure'` Microsoft Azure (Big Data Program and ECMWF open data)
- `'ecmwf'` ECMWF open data products
- `'aws-old'` File name formats change. This is so Herbie can find old GFS filenames.
- `'pando'` University of Utah Pando Archive (gateway 1)
- `'pando2'` University of Utah Pando Archive (gateway 2)

The default config file doesn't specify a priority. Instead, Herbie loops through the sources in the order they are listed in each [model template file](https://github.com/blaylockbk/Herbie/tree/main/herbie/models). Herbie tries to find the GRIB file at the first source, and then looks at subsequent sources in order until the requested file is found.

This configure option allows you to specify a different order to look for data or only look in certain locations. For example, if you only want to download the real-time data from NOMADS, then set

```toml
priority = ['nomads']
```

Or you can change the order sources are checked

```toml
priority = ['google', 'nomads', 'aws']
```

But beware; setting a default priority might prevent you from checking all available sources.

> **📝 Default Download Priority Rational**
> 
> The default download priority order for HRRR is 
> ```
> ['aws', 'nomads', 'google', 'azure', 'pando', 'pando2']
> ```
> because I anticipate a user will most often request model grids from the recent past or earlier rather than relying on Herbie for operational, real-time needs.
> 
> While NOMADS is the official operational source of model output data and has the most recent model output available, NOMADS only retains data for a few days, so likely won't have the data you are looking for. Furthermore, NOMADS will throttle the download speed or block users who violate their usage agreement and download too much data within an hour. For most cases, it makes sense to look for the data on AWS first, then look for it at other sources. 
> 
> I should also say that I don't have any preference over AWS, Google, or Azure.
 
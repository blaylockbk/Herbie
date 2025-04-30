# Herbie CLI

The Herbie Command Line Interface (CLI) provides easy access to archived Numerical Weather Prediction (NWP) model data through a simple command-line tool. It leverages the Herbie Python package to search for, inspect, and download GRIB2 files from various data sources.

## Installation

The CLI is installed automatically when you install the Herbie package:

```bash
pip install herbie-data
```

You may also install it as a tool with uv

```bash
uv tool install herbie-data
```

Or use it with uvx

```bash
uvx --from herbie-data herbie
```

## Basic Usage

Show all the options with `--help`

```bash
herbie --help
```

The basic usage is:

```bash
herbie COMMAND [OPTIONS]
```

## Available Commands

| Command     | Description                                  |
| ----------- | -------------------------------------------- |
| `data`      | Find and show a GRIB2 file URL.              |
| `index`     | Find and show a GRIB2 index file URL.        |
| `inventory` | Show inventory of GRIB2 fields or subset.    |
| `download`  | Download GRIB2 file or subset.               |
| `sources`   | Return JSON of possible GRIB2 source URLs.   |
| `plot`      | Quick plot of GRIB2 field (Not implemented). |

## Examples

```bash
# Get the URL for a HRRR surface file from today at 12Z
herbie data -m hrrr --product sfc -d "2023-03-15 12:00" -f 0

# Download GFS 0.25° forecast hour 24 temperature at 850mb
herbie download -m gfs --product 0p25 -d 2023-03-15T00:00 -f 24 --subset ":TMP:850 mb:"

# View all available variables in a RAP model run
herbie inventory -m rap -d 2023031512 -f 0

# Download multiple forecast hours for a date range
herbie download -m hrrr -d 2023-03-15T00:00 2023-03-15T06:00 -f 1 3 6 --subset ":UGRD:10 m:"

# Specify custom source priority (check only Google)
herbie data -m hrrr -d 2023-03-15 -f 0 -p google
```

## Common Arguments

All commands support the following arguments:

### Required Arguments

| Argument       | Description                          |
| -------------- | ------------------------------------ |
| `-d`, `--date` | Model initialization date (required) |
|                |                                      |

### Optional Arguments

| Argument           | Description                        | Default         |
| ------------------ | ---------------------------------- | --------------- |
| `-m`, `--model`    | The name of the NWP model          | `hrrr`          |
| `--product`        | Product type specific to the model | model's default |
| `-f`, `--fxx`      | Forecast hour(s)                   | `[0]`           |
| `-p`, `--priority` | Data source priority order         | model's default |
| `--verbose`        | Enable verbose output              | `False`         |

Some commands accept additional arguments:

| Command                         | Additional Arguments                                                                                     |
| ------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `inventory`, `download`, `plot` | `--subset`: Search string for filtering variables                                                        |
| `download`                      | `--save_dir`: The root directory to save downloaded files.\n`--overwrite`: Replace existing GRIB2 files. |
|                                 |                                                                                                          |

## Global Options

| Option            | Description                              |
| ----------------- | ---------------------------------------- |
| `-v`, `--version` | Show Herbie version number               |
| `--show_versions` | Show versions of Herbie and dependencies |
|                   |                                          |

## Detailed Argument Reference

### Date Format (`-d`, `--date`)

The date argument accepts multiple formats:

- `YYYYMMDDHH` (e.g., `2023031500`)
- `YYYY-MM-DD` (e.g., `2023-03-15`, assumes 00Z)
- `YYYY-MM-DDTHH:MM` (e.g., `2023-03-15T12:00`)
- `"YYYY-MM-DD HH:MM"` (e.g., `"2023-03-15 12:00"`)

You can also specify multiple dates for batch processing:

```bash
herbie data -d 2023-03-15T00:00 2023-03-15T06:00 2023-03-15T12:00 -m hrrr -f 0
```

### Model (`-m`, `--model`)

The model argument specifies which NWP model to use. Common options include:

| Model  | Description                                        |
| ------ | -------------------------------------------------- |
| `hrrr` | High-Resolution Rapid Refresh (3km CONUS)          |
| `gfs`  | Global Forecast System (global coverage)           |
| `rap`  | Rapid Refresh (13km CONUS)                         |
| `nam`  | North American Mesoscale (12km North America)      |
| `rrfs` | Rapid Refresh Forecast System                      |
| `ifs`  | European Centre for Medium-Range Weather Forecasts |
| `nwm`  | National Water Model                               |

### Product Type (`--product`)

The product type is model-specific and determines which variant of the model output to use.

Some examples:

#### HRRR Products

- `sfc` - Surface fields (2D)
- `prs` - Pressure level fields (3D)
- `nat` - Native model level fields (3D)
- `subh` - Subhourly fields (15min)

#### GFS Products

- `0p25` - 0.25° resolution
- `0p50` - 0.50° resolution
- `1p00` - 1.00° resolution

If not specified, Herbie will use the default product for the selected model.

### Forecast Hour (`-f`, `--fxx`)

Forecast hour represents the number of hours into the future that the model is predicting. You can specify a single forecast hour or multiple hours:

```bash
herbie download -m hrrr -d 2023-03-15T00:00 -f 0 1 3 6 12
```

Available forecast hours vary by model.

### Data Source Priority (`-p`, `--priority`)

Herbie can download data from multiple archive sources. You can control the order in which these sources are checked:

```bash
herbie data -m hrrr -d 2023-03-15 -f 0 -p aws nomads
```

Available data sources:

| Source   | Description                                    |
| -------- | ---------------------------------------------- |
| `aws`    | Amazon Web Services (NOAA Open Data Program)   |
| `google` | Google Cloud Platform (NOAA Open Data Program) |
| `nomads` | NOAA NOMADS server                             |
| `azure`  | Microsoft                                      |
| `ecmwf`  | ECMWF Open-data                                |
| others   |                                                |

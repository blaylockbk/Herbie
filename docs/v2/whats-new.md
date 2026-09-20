# ✨ What's New

Herbie v2 introduces major architectural improvements, better performance, and several new features designed to make working with numerical weather prediction (NWP) data easier and more flexible.

The v2 API was introduced with Herbie 2026.6.0, and is imported as follows

```python
from herbie.v2 import Herbie
```

Herbie v2 introduces:

- faster inventory processing with **Polars**
- improved CLI and terminal output via **Rich**
- a redesigned **model template system**
- new **FastHerbie custom GRIB building**
- better **parallel downloads**
- improved **Jupyter notebook display**
- support for **Zarr model sources**
- more flexible **inventory filtering**


# Major Changes

## New Dependencies

Herbie now uses two additional core dependencies:

- **Polars** — used instead of Pandas for inventory tables and data manipulation.
  Polars provides better performance and a cleaner expression-based API.

- **Rich** — used to provide improved terminal output, including formatted tables and progress bars.

Additional packages are needed for zarr support:

```bash
pip install herbie[zarr]
```

---

## New Default Data Directory

The default download directory has changed to:

```
~/herbie-data/
```

Downloaded files now preserve the **original directory structure of the data source**, which makes it easier to mirror remote archives locally and pre-populate the cache using tools like `rclone`.

---

## New Import Structure

Herbie is now a **namespace containing model-specific classes**.

### Example

```python
from herbie.v2 import Herbie

H = Herbie.HRRR('2025-01-01')
```

You may also import a specific model directly:

```python
from herbie.v2 import HRRR

H = HRRR('2025-01-01')
```

This architecture simplifies the addition of new model templates, and enables model-specific docstrings in your IDE.

---

# Configuration

## Herbie Config File

Herbie now supports a **configuration file** for controlling settings such as:

- data directory
- preferred data sources
- other runtime options

This allows users to customize Herbie behavior without modifying code.

Config files are written to `herbie.toml` file in your active directory, or maybe included in the `pyproject.toml` file

---

# Forecast Lead Time (`step`)

The `fxx` parameter has been renamed to **`step`**.

`step` represents the forecast lead time and may be specified as either:

- an integer number of hours
- a `timedelta` object

### Example

```python
from herbie.v2 import Herbie
from datetime import datetime, timedelta

H = Herbie.HRRR('2025-01-01', step=12)

H = Herbie.HRRR(datetime(2025, 1, 1), step=timedelta(hours=12))
```

---

# Jupyter Notebook Display

Herbie objects now provide a **rich HTML representation** when displayed in Jupyter notebooks.

The display summarizes:

- selected model parameters
- forecast time
- available data sources
- file status

This makes interactive exploration significantly easier.

---

# Model Template System

Model templates have been redesigned.

Templates are now implemented as subclasses of a base class:

```
HerbieModel
```

This simplifies:

- adding support for new models
- maintaining model metadata
- extending model-specific behavior

---

# Inventory Improvements

Inventory tables are now powered by **Polars DataFrames**.

### Benefits

- faster performance
- expression-based filtering
- easier data manipulation

Users can now filter inventory records using **Polars expressions across any column**, rather than being limited to searching a single field.

Additionally, inventory records now include:

- **data source**
- **index source**

This enables downloading fields from multiple GRIB files and combining them into custom datasets.

---

# Download Improvements

## Parallel Subset Downloads

Subset downloads now run in **parallel threads**, with one thread per subset group.

This can significantly improve download performance when retrieving many fields.

---

## Rich Progress Bars

Downloads now include **Rich-powered progress bars**, providing clear feedback during large downloads.

---

## Source-Preserving File Paths

Downloaded files now preserve their **original remote paths** within `~/herbie-data/`.

This allows users to:

- mirror remote archives locally
- use external tools like `rclone`
- easily reuse cached datasets

---

# xarray Integration

When loading GRIB data with multiple hypercubes, Herbie now returns an **xarray DataTree**.

This provides a structured representation of complex GRIB files containing multiple variables or grids.

---

# Source Status Checking

Herbie now includes tools for checking data availability across sources.

## Display Source Status

```python
H.status()
```

This shows:

- available data sources
- which sources have been checked
- whether files exist

---

## Resolve Data Sources

You can manually check which source contains the data.

```python
# Find first available file
H.resolve()

# Check a specific source
H.resolve('google')

# Check all sources
H.resolve('all')
```

---

# FastHerbie (Major New Feature)

`FastHerbie` has been completely redesigned.

It now enables **building custom GRIB files** by combining fields from many model files.

### How it works

1. Inventory tables from multiple files are concatenated
2. Downloads occur in parallel
3. Selected fields are merged into a new GRIB file

### Example Use Cases

- Retrieve **all 6-hour TMP:2 m forecasts for a day** into one file
- Retrieve **all GRD:10 m forecasts initialized at a single time**

This provides a powerful way to generate tailored datasets without manually managing GRIB files.

---

# Zarr Support

Infrastructure has been added to support **Zarr-based model data sources**.

Example:

```python
Herbie.HRRR.from_zarr('dynamical', 'analysis')
```

This enables future support for cloud-native model datasets.


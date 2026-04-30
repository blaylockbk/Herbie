# New Herbie

New Dependencies

- Polars: I much prefer using this DataFrame library over Pandas.
- Rich: For printing information for the user in a fancy way.

The default save directory is now `~/herbie-data/`

```python
from herbie.v2 import Herbie
```

Herbie is now a namespace, with many model HerbieModel classes for different models.

```python
H = Herbie.HRRR('2025-01-01')
```

you may also just import the model you want to use instead

```python
from herbie.v2 import HRRR
H = HRRR('2025-01-01')
```

## `fxx` is now `step`

The forecast lead time is now controlled with the step parameter, and may be a timedelta object (which is converted to integer hours). The following are equivalent:

```python
from herbie.v2 import Herbie
from datetime import datetime, timedelta

H = Herbie.HRRR('2025-01-01', step=12)

H = Herbie.HRRR(datetime(2025,1,1), step=timedelta(hours=12))
```

## Notebook HTML Representor

For convenient user exploration, when displaying a Herbie object in a Jupyter Notebook, there is a new HTML display showing the parameters selected and sources.

## Model Templates

Big change to the model templates. These are subclassed from the base class HerbieModel.

## Inventory

Use Polars as the DataFrame. I'm a big Polars fan, and find it much easier to read and write than Pandas.

Since I'm using Polars for the DataFrame, users can filter the inventory with expressions for each column rather than just the "search_this" column.

The data and index source are now included in the inventory dataframe. This will enable downloading fields from multiple files and "build your own GRIB files."

## Download

Download for subsets are now done with multiple threads, one thread for each subset group.

Use rich progress bars for downloads.

Remote file paths are preserved rather than specifying a custom data path. I wanted to make it possible to use rclone to quickly pre-fill your `herbie-data/` directory, then use Herbie to access those files locally.

## xarray

Multiple hypercubes are returned as a DataTree.

## status

Display the sources and which sources have been checked and if the files exist.

## resolve

Manually check if files exist

```python
# Find first available file
H.resolve()

# Check specific source
H.resolve('google')

# Check all
H.resolve('all')
```

## FastHerbie

This behaves _very_ different. Inventory DataFrames are concatted together for many files, then parallel downloads happen and join the fields into a new, custom grib file. It's a "build your own GRIB" feature.

Examples:

- Get all 6-hr `TMP:2 m` forecasts for the day in one file.
- Get all `GRD:10 m` forecasts initialized at a single time.

## Zarr Support

Built infrastructure to support access to Zarr model sources

```python
Herbie.HRRR.from_zarr('dynamical', 'analysis')
```

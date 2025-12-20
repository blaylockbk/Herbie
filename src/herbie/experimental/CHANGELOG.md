# New Herbie

New Dependencies

- Polars: I much prefer using this DataFrame library over Pandas.
- Rich: For printing information for the user in a fancy way.

The default save directory is now `~/herbie-data/`

# Model Templates

Big change to the model templates. These are subclassed from the base class ModelTemplate.

ModelTemplate is now responsible for finding existing GRIB and Index files.

## Inventory

Use Polars as the DataFrame. I'm a big Polars fan, and find it much easier to read and write than Pandas.

Since I'm using Polars for the DataFrame, users can filter the inventory with expressions for each column rather than just the "search_this" column.

The data and index source are now included in the inventory dataframe. This will enable downloading fields from multiple files and "build your own GRIB files."

## Download

Download for subsets are now done with multiple threads, one thread for each subset group.

Use rich progress bars for downloads.

Remote file paths are preserved rather than specifying a custom data path. I wanted to make it possible to use rclone to quickly pre-fill your `herbie-data/` directory, then use Herbie to access those files locally. 

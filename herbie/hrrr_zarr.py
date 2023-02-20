"""
Some initial work to use Herbie to access HRRR-Zarr.
Code from Brian Blaylock and Taylor Gowan.

The directory structure is very different from the GRIB2 format.

- https://hrrrzarr.s3.amazonaws.com/index.html
- https://mesowest.utah.edu/html/hrrr/
- https://mesowest.utah.edu/html/hrrr/zarr_documentation/html/python_data_loading.html
- https://mesowest.utah.edu/html/hrrr/zarr_documentation/html/xarray_one_day_analysis_example.html
- https://github.com/ProjectPythia/intake-cookbook/tree/main/notebooks
"""
import datetime

import cartopy.crs as ccrs
import pandas as pd
import s3fs
import xarray as xr


def load_dataset(urls):
    """
    We use xarray's `open_mfdataset` to load the data. There's a couple of things
    missing from the metadata, so we use a metpy extension to add projection info
    and latitude/longitude. We also promote the "time" attribute to a coordinate
    so that combining the datasets for each hour will work later on.
    """
    projection = ccrs.LambertConformal(
        central_longitude=262.5,
        central_latitude=38.5,
        standard_parallels=(38.5, 38.5),
        globe=ccrs.Globe(semimajor_axis=6371229, semiminor_axis=6371229),
    )

    fs = s3fs.S3FileSystem(anon=True)
    ds = xr.open_mfdataset([s3fs.S3Map(url, s3=fs) for url in urls], engine="zarr")
    ds = ds.rename(projection_x_coordinate="x", projection_y_coordinate="y")
    ds = ds.metpy.assign_crs(projection.to_cf())
    ds = ds.metpy.assign_latitude_longitude()
    ds = ds.set_coords("time")
    return ds


def load_combined_dataset(start_date, num_hours, level, param_short_name):
    """
    Format the URLs to load the data, and combine the hours using `xarray.concat`.
    Note that because there's an extra level of nesting for the main data variable
    (level and variable name), we have to get both the zarr group url and the url
    for the nested subgroup. That's why we have to use `open_mfdataset`: "mf"
    means "multifile") - other zarr datasets likely won't have this quirk.
    """
    combined_ds = None
    for i in range(num_hours):
        time = start_date + datetime.timedelta(hours=i)
        group_url = time.strftime(
            f"s3://hrrrzarr/sfc/%Y%m%d/%Y%m%d_%Hz_anl.zarr/{level}/{param_short_name}"
        )
        subgroup_url = f"{group_url}/{level}"
        partial_ds = load_dataset([group_url, subgroup_url])
        if not combined_ds:
            combined_ds = partial_ds
        else:
            combined_ds = xr.concat(
                [combined_ds, partial_ds], dim="time", combine_attrs="drop_conflicts"
            )
    return combined_ds


def demo_tmp2m():
    # Let's grab an analysis file.
    ds = load_combined_dataset(
        start_date=pd.to_datetime("2021-07-03 12:00"),
        num_hours=4,
        level="2m_above_ground",
        param_short_name="TMP",
    )

    print(ds)
    ds.info()
    print()
    print(ds.coords)
    print()
    print(ds.data_vars)
    print()
    print(ds["TMP"])


if __name__ == "__main__":
    demo_tmp2m()

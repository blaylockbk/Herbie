## Brian Blaylock
## July 29, 2021

"""
Some initial work to use Herbie to access HRRR-Zarr

The directory structure is very different than the GRIB2 format.

- https://hrrrzarr.s3.amazonaws.com/index.html
- https://mesowest.utah.edu/html/hrrr/

"""

import pandas as pd
import s3fs
import xarray as xr

# Let's grab an analysis file using s3fs

fs = s3fs.S3FileSystem(anon=True)

date = pd.to_datetime("2021-07-03 12:00")
level = "2m_above_ground"
var = "TMP"

url = f"hrrrzarr/sfc/{date:%Y%m%d}/{date:%Y%m%d_%H}z_anl.zarr/{level}/{var}/{level}/"
store = s3fs.S3Map(root=url, s3=fs, check=False)
ds = xr.open_zarr(store)

ds.TMP.plot()

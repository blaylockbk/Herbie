# ⚡ What about Zarr?

When it comes to subsetting large datasets, GRIB has some limitations. The [Zarr](https://zarr.readthedocs.io/en/stable/) data format, however, makes downloading small chunks of large, gridded dataset easy. Herbie does not download Zarr data, but it could in the future (pull request anyone?). 

Unfortunately, weather data is not widely available in Zarr format—except for at least one model. 

## HRRR-Zarr

Select parts of the HRRR model archive are available in Zarr format in the `s3://hrrrzarr` bucket on AWS developed by [Taylor Gowan](https://twitter.com/tayloragowan) and managed by the MesoWest group at the University of Utah. If you are using large amounts of the HRRR dataset and need to do a lot of subsetting, you might find this dataset useful. 

- [HRRR-Zarr Documentation](https://mesowest.utah.edu/html/hrrr/) by *University of Utah - Mesowest*
- [HRRR-Zarr Examples](https://github.com/taylorgowan/zarr) by *Taylor Gowan* 
- [HRRR-Zarr AMS Short Course](https://github.com/ktyle/python_pangeo_ams2021/blob/main/notebooks/03_Pangeo_HRRR.ipynb) by *Kevin Tyle*
- [HRRR-Zarr Sandbox](https://github.com/blaylockbk/Herbie/blob/main/notebooks/zarr_HRRR.ipynb) by *Brian Blaylock*

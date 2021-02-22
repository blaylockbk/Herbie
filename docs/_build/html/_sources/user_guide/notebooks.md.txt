# 📝 Jupyter Notebooks

These notebooks show practical use case of the `hrrrb` package:

- [Main Package Examples](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/examples.ipynb)
- [Make Cartopy maps with HRRR data](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_plot-on-map-with-common-features.ipynb)

Select variables of the HRRR archive are available in Zarr format (managed by the MesoWest group at the University of Utah). I'm still trying to understand how to use it, but here is a notebook showing my exploring...
- [HRRR in Zarr format](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/zarr_HRRR.ipynb)

The following notebooks offer a deeper discussion on how the download process works. These are not intended for practical use, but should help illustrate my thought process when I created this package.

- [Part 1: How to download a bunch of HRRR grib2 files (full file)](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part1.ipynb)
- [Part 2: How to download a subset of variables from a HRRR file](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part2.ipynb)
- [Part 3: A function that can download many full files, or subset of files](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part3.ipynb)
- [Part 4: Opening GRIB2 files in Python with xarray and cfgrib](https://github.com/blaylockbk/HRRR_archive_download/blob/master/notebooks/demo_download_hrrr_archive_part4.ipynb)

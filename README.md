<div
  align="center"
>

![](https://github.com/blaylockbk/Herbie/blob/master/docs/_static/HerbieLogo2_tan_transparent.png?raw=true)

# Herbie: Retrieve NWP Model Data

<!-- Badges -->
[![](https://img.shields.io/pypi/v/herbie-data)](https://pypi.python.org/pypi/herbie-data/)
![](https://img.shields.io/github/license/blaylockbk/Herbie)
[![DOI](https://zenodo.org/badge/275214142.svg)](https://zenodo.org/badge/latestdoi/275214142)
<!--[![Join the chat at https://gitter.im/blaylockbk/Herbie](https://badges.gitter.im/blaylockbk/Herbie.svg)](https://gitter.im/blaylockbk/Herbie?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)-->
<!-- (Badges) -->

</div>

The [NOAA Big Data Program](https://www.noaa.gov/information-technology/big-data) has made weather data more accessible than ever before. **Herbie** is a python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources. Herbie helps you discover and download High Resolution Rapid Refresh (HRRR), Rapid Refresh (RAP), Global Forecast System (GFS), National Blend of Models (NBM), and Rapid Refresh Forecast System - Prototype (RRFS). NWP data is usually in GRIB2 format and can be read with xarray/cfgrib.

# 📔 [Herbie Documentation](https://blaylockbk.github.io/Herbie/_build/html/)

## Install

Requires cURL and **Python 3.8+** with requests, numpy, pandas, xarray, and cfgrib. Optional packages are matplotlib, cartopy, and [Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop).

```bash
pip install herbie-data
```
or
```bash
pip install git+https://github.com/blaylockbk/Herbie.git
```

or, create the provided **[conda environment](https://github.com/blaylockbk/Herbie/blob/master/environment.yml)**.

## Capabilities

- Search different data sources for model output.
- Download full GRIB2 files
- Download subset GRIB2 files (by grib field)
- Read data with xarray
- Plot data with Cartopy (very early development)

```python
from herbie.archive import Herbie

# Herbie object for the HRRR model 6-hr surface forecast product
H = Herbie('2021-01-01 12:00',
           model='hrrr',
           product='sfc',
           fxx=6)

# Download the full GRIB2 file
H.download()

# Download a subset, like all fields at 500 mb
H.download(":500 mb")

# Read subset with xarray, like 2-m temperature.
H.xarray("TMP:2 m")
```

## Data Sources

Herbie downloads model data from the following sources, but can be extended to include others:

- NOMADS
- Big Data Program Partners (AWS, Google, Azure)
- University of Utah CHPC Pando archive

## History

During my PhD at the University of Utah, I created, at the time, the [only publicly-accessible archive of HRRR data](http://hrrr.chpc.utah.edu/). In the later half of 2020, this data was made available through the [NOAA Big Data Program](https://www.noaa.gov/information-technology/big-data). This package organizes and expands my original download scripts into a more coherent package with the ability to download HRRR and RAP model data from different data sources. It will continue to evolve at my own leisure.

I originally released this package under the name "HRRR-B" because it only dealt with the HRRR data set, but I have addeed ability to download RAP data. Thus, it was rebranded with the name "Herbie" as a model download assistant. For now, it is still called "hrrrb" on PyPI because "herbie" is already taken. Maybe someday, with some time and an enticing reason, I'll add additional download capabilities. 

### Alternative Download Tools

As an alternative you can use [rclone](https://rclone.org/) to download files from AWS or GCP. I quite like rclone. Here is a [short rclone tutorial](https://github.com/blaylockbk/pyBKB_v3/blob/master/rclone_howto.md)

---

Thanks for using Herbie, and Happy Racing 🏎🏁

\- Brian  

👨🏻‍💻 [Contributing Guidelines](https://blaylockbk.github.io/Herbie/_build/html/user_guide/contribute.html)  
💬 [GitHub Discussions](https://github.com/blaylockbk/Herbie/discussions)  
🚑 [GitHub Issues](https://github.com/blaylockbk/Herbie/issues)  
🌐 [Personal Webpage](http://home.chpc.utah.edu/~u0553130/Brian_Blaylock/home.html)  
🌐 [University of Utah HRRR archive](http://hrrr.chpc.utah.edu/)  

> ### ✒ Pando HRRR Archive citation:
>
> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. https://doi.org/10.1016/j.cageo.2017.08.005

P.S. If you like Herbie, check out my [GOES-2-go](https://github.com/blaylockbk/goes2go) package to download GOES-East/West data and [SynopticPy](https://github.com/blaylockbk/SynopticPy) to download mesonet data from the Synoptic API.

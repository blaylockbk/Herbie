<div
  align="center"
>

<img 
  src="https://github.com/blaylockbk/Herbie/raw/main/images/Herbie_transparent_tan.svg" 
  style="filter: drop-shadow(0px 0px 5px #000000)">

# Herbie: Retrieve NWP Model Data 🏁

<!-- Badges -->
[![](https://img.shields.io/pypi/v/herbie-data)](https://pypi.python.org/pypi/herbie-data/)
![](https://img.shields.io/github/license/blaylockbk/Herbie)
[![DOI](https://zenodo.org/badge/275214142.svg)](https://zenodo.org/badge/latestdoi/275214142)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

<!-- (Badges) -->

</div>

**Herbie** is a python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources. **Its most popular capability is to download HRRR model data.** NWP data in GRIB2 format can be read with xarray+cfgrib. Much of this data is made available through the [NOAA Open Data Dissemination](https://www.noaa.gov/information-technology/open-data-dissemination) (NODD) Program (formerly the Big Data Program) which has made weather data more accessible than ever before.

Herbie helps you discover, download, and read data from:
- [High Resolution Rapid Refresh (HRRR)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrr.html) | [HRRR-Alaska](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_hrrrak.html)
- [Rapid Refresh (RAP)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rap.html)
- [Global Forecast System (GFS)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gfs.html)
- [Global Ensemble Forecast System (GEFS)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_gefs.html)
- [ECMWF Open Data Forecast Products](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_ecmwf.html)
- [National Blend of Models (NBM)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_nbm.html)
- [Rapid Refresh Forecast System - Prototype (RRFS)](https://blaylockbk.github.io/Herbie/_build/html/user_guide/notebooks/data_rrfs.html)

# 📓 [Herbie Documentation](https://blaylockbk.github.io/Herbie/_build/html/)

## Install

Herbie requires cURL and **Python 3.8+** with requests, numpy, pandas, xarray, and cfgrib. Optional packages are matplotlib, cartopy, and [Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop).

```bash
pip install herbie-data
```
or
```bash
pip install git+https://github.com/blaylockbk/Herbie.git
```

You may also create the provided **[conda environment](https://github.com/blaylockbk/Herbie/blob/main/environment.yml)**.

```bash
wget https://github.com/blaylockbk/Herbie/raw/main/environment.yml
conda env create -f environment.yml
```

## Capabilities

- Search for model output from different data sources.
- Download full GRIB2 files.
- Download subset GRIB2 files (by grib field).
- Read data with xarray.
- Read index file with Pandas.
- Plot data with Cartopy (very early development).


```mermaid
  graph TD;
      d1[(HRRR)] -.-> H
      d2[(RAP)] -.-> H
      d3[(GFS)] -.-> H
      d33[(GEFS)] -.-> H
      d4[(ECMWF)] -.-> H
      d5[(NBM)] -.-> H
      d6[(RRFS)] -.-> H
      H((Herbie))
      H --- .download
      H --- .xarray
      H --- .read_idx

      style H fill:#d8c89d,stroke:#0c3576,stroke-width:4px,color:#000000
```

```python
from herbie import Herbie

# Herbie object for the HRRR model 6-hr surface forecast product
H = Herbie(
  '2021-01-01 12:00',
  model='hrrr',
  product='sfc',
  fxx=6
)

# Download the full GRIB2 file
H.download()

# Download a subset, like all fields at 500 mb
H.download(":500 mb")

# Read subset with xarray, like 2-m temperature.
H.xarray("TMP:2 m")
```

## Data Sources

Herbie downloads model data from the following sources, but can be extended to include others:

- [NOMADS](https://nomads.ncep.noaa.gov/)
- Big Data Program Partners (AWS, Google, Azure)
- ECMWF Open Data Azure storage
- University of Utah CHPC Pando archive
- Local file system

## History

During my PhD at the University of Utah, I created, at the time, the [only publicly-accessible archive of HRRR data](http://hrrr.chpc.utah.edu/). Over 1,000 research scientists and professionals used that archive.

<blockquote><cite>
<p style="padding-left: 22px ; text-indent: -22px ;"> Blaylock B., J. Horel and S. Liston, 2017: Cloud Archiving and Data Mining of High Resolution Rapid Refresh Model Output. Computers and Geosciences. 109, 43-50. <a href="https://doi.org/10.1016/j.cageo.2017.08.005">https://doi.org/10.1016/j.cageo.2017.08.005</a></p>
</cite></blockquote>

In the later half of 2020, the HRRR dataset from 2014 to present was made available through the [NOAA Big Data Program](https://www.noaa.gov/information-technology/big-data). Herbie organizes and expands my original download scripts into a more coherent package with the extended ability to download data for other models from many different archive sources.

I originally released this package under the name “HRRR-B” because it only worked with the HRRR dataset; the “B” was for my first-name initial. Since then, I have added the ability to download RAP, GFS, ECMWF, GEFS, RRFS, and others with potentially more models in the future. Thus, this package was renamed ***Herbie***, named after one of my favorite childhood movie characters. 

The University of Utah MesoWest group now manages a [HRRR archive in Zarr format](http://hrrr.chpc.utah.edu/). Maybe someday, Herbie will be able to take advantage of that archive.

---

**Thanks for using Herbie, and happy racing!**

🏁 Brian


<br>

|||
|:----:|---|
| 👨🏻‍💻 | [Contributing Guidelines](https://blaylockbk.github.io/Herbie/_build/html/user_guide/contribute.html)  
| 💬 | [GitHub Discussions](https://github.com/blaylockbk/Herbie/discussions)  
| 🚑 | [GitHub Issues](https://github.com/blaylockbk/Herbie/issues)  
| 🌐 | [Personal Webpage](http://home.chpc.utah.edu/~u0553130/Brian_Blaylock/home.html)  
| 🌐 | [University of Utah HRRR archive](http://hrrr.chpc.utah.edu/) 

Cite Herbie: 

    Blaylock, B. K., 2022: Herbie: Retrieve Numerical Weather Prediction     
    Model Data [Computer software]. https://doi.org/10.5281/zenodo.6526110.

<br>

P.S. If you like Herbie, check out my other repos:
- [🌎 GOES-2-go](https://github.com/blaylockbk/goes2go): A python package to download GOES-East/West data and make RGB composites.
- [🌡 SynopticPy](https://github.com/blaylockbk/SynopticPy): A python package to download mesonet data from the Synoptic API.
- [🔨 Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop): A python package with various tools I made that are useful (like easy funxtions to build Cartopy maps).
- [💬 Bubble Print](https://github.com/blaylockbk/BubblePrint): A silly little python package that gives your print statement's personality.
- [📜 MET Syntax](https://github.com/blaylockbk/vscode-met-syntax): An extension for Visual Studio Code that gives syntax highlighting for Model Evaluation Tools (MET) configuration files.

> **Note**: Alternative Download Tools  
> As an alternative to Herbie, you can use [rclone](https://rclone.org/) to download files from AWS or GCP. I love rclone. Here is a short [rclone tutorial](https://github.com/blaylockbk/pyBKB_v3/blob/master/rclone_howto.md)

---
title: 'Herbie: A Python package to retrieve numerical weather prediction model data'
tags:
  - Python
  - meteorology
  - xarray
  - grib
authors:
  - name: Brian Blaylock
    orcid: 0000-0003-2133-9313
date: 21 March 2025
bibliography: paper.bib
---

# Summary

**Herbie** is a Python package that downloads recent and archived numerical weather prediction (NWP) model output from different cloud archive sources. NWP data is distributed in GRIB2 format which Herbie reads using xarray+cfgrib. Herbie also provides some extra features to help visualize and extract data.

# Statement of need

Python library to locate NWP data from a multitude of source locations.
- NOMADS
- Public cloud (AWS, GCP, Azure)

# History

During my PhD at the University of Utah, I created, at the time, the [only publicly-accessible archive of HRRR data](http://hrrr.chpc.utah.edu/). Over 1,000 research scientists and professionals used that archive. Herbie was then developed to access HRRR data from that archive and was first used on the Open Science Grid.

In the later half of 2020, the HRRR dataset from 2014 to present was made available through the [NODD Open Data Dissemination Program](https://www.noaa.gov/information-technology/open-data-dissemination) (formerly NOAA's Big Data Program). The latest version of Herbie organizes and expands my original download scripts into a more coherent package with the extended ability to download data for other models from many different archive sources, and it will continues to evolve.

I originally released this package under the name “HRRR-B” because it only worked with the HRRR dataset; the “B” was for Brian. Since then, I have added the ability to download many more models including RAP, GFS, ECMWF, GEFS, and RRFS with the potential to add more models in the future. Thus, this package was renamed **_Herbie_**, named after one of my favorite childhood movies.

The University of Utah MesoWest group now manages a [HRRR archive in Zarr format](http://hrrr.chpc.utah.edu/). Maybe someday, Herbie will be able to take advantage of that archive.

# Acknowledgements


# References

- https://doi.org/10.1016/j.cageo.2017.08.005
- https://doi.org/10.1175/JTECH-D-18-0073.1

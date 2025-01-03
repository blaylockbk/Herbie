# HRRR: High Resolution Rapid Refresh

- [HRRR Homepage (ESRL)](https://rapidrefresh.noaa.gov/hrrr/ "Details about the HRRR model and graphics for the most recent runs.")
- [GSL-Regional-Model-Forum (GitHub)](https://github.com/NOAA-GSL/GSL-Regional-Model-Forum/discussions/ "Ask the HRRR model developers and the community about the HRRR model.")

> Dowell, D. C., and Coauthors, 2022: The High-Resolution Rapid Refresh (HRRR): An Hourly Updating Convection-Allowing Forecast Model. Part I: Motivation and System Description. Wea. Forecasting, **37**, 1371–1395, <https://doi.org/10.1175/WAF-D-21-0151.1>.

> James, E. P., and Coauthors, 2022: The High-Resolution Rapid Refresh (HRRR): An Hourly Updating Convection-Allowing Forecast Model. Part II: Forecast Performance. Wea. Forecasting, **37**, 1397–1417, <https://doi.org/10.1175/WAF-D-21-0130.1>.

> James, E. P., and S. G. Benjamin, 2017: Observation system experiments with the hourly updating Rapid Refresh model using GSI hybrid ensemble-variational data assimilation. Mon. Wea. Rev., **145**, 2897–2918, <https://doi.org/10.1175/MWR-D-16-0398.1>.

## Data Sources

| `prioriy=` | Data source                                                                                                           | Archive Duration      |
| ---------- | --------------------------------------------------------------------------------------------------------------------- | --------------------- |
| `"aws"`    | [Amazon Web Services](https://registry.opendata.aws/noaa-hrrr-pds/)                                                   | 2014-07-30 to present |
| `"nomads"` | [NOMADS](https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/)                                                   | Yesterday and today   |
| `"google"` | [Google Cloud Platform ](https://console.cloud.google.com/marketplace/product/noaa-public/hrrr?project=python-232920) | 2014-07-30 to present |
| `"azure"`  | [Microsoft Azure](https://github.com/microsoft/AIforEarthDataSets/blob/main/data/noaa-hrrr.md)                        | 2021-03-21 to present |
| `"pando"`  | [University of Utah Pando archive](https://home.chpc.utah.edu/~u0553130/Brian_Blaylock/cgi-bin/hrrr_download.cgi)     | varies                |

## Model Initialization

Model cycles every hour.

## Forecast Hour

For the most recent version of HRRR...

| `fxx=`                   | Forecast lead time                                   |
| ------------------------ | ---------------------------------------------------- |
| `0` through `48`, step=1 | available for runs initialized at 00z, 06z, 12z, 18z |
| `0` through `18`, step=1 | available for runs initialized at all other hours.   |

## Products

| `product=` | Product Description |
| ---------- | ------------------- |
| `"sfc"`    | surface fields      |
| `"prs"`    | pressure levels     |
| `"nat"`    | native levels       |
| `"subh"`   | subhourly products  |

## Update History

| Version | Start      |
| ------- | ---------- |
| HRRRv1  | 2014-09-30 |
| HRRRv2  | 2016-08-23 |
| HRRRv3  | 2018-07-12 |
| HRRRv4  | 2020-12-02 |
| RRFS    | 2026       |
|         |            |

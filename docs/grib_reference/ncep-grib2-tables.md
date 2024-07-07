# NCEP GRIB2 Tables

> **🚧 Work in progress** My intent is to make this reference useful for people unfamiliar with GRIB and Herbie's search argument used for filtering data.

A selection from [ON388 - TABLE 2: PARAMETERS & UNITS](https://www.nco.ncep.noaa.gov/pmb/docs/on388/table2.html)

See also [HRRR GRIB2 Tables](https://home.chpc.utah.edu/~u0553130/Brian_Blaylock/HRRR_archive/hrrr_sfc_table_f00-f01.html)

 | Variable | Description                                       | Units         |
 | -------- | ------------------------------------------------- | ------------- |
 | PRES     | Pressure                                          | Pa            |
 | PRMSL    | Pressure reduced to MSL                           | Pa            |
 | PTEND    | Pressure tendency                                 | Pa/s          |
 | PVORT    | Potential vorticity                               | K m2 kg-1 s-1 |
 | HGT      | Geopotential height                               | gpm           |
 | DIST     | Geometric height                                  | m             |
 | REFC     | Maximum/Composite radar reflectivity              | dbZ           |
 | TOZNE    | Total ozone                                       | Dobson        |
 | TMP      | Temperature                                       | K             |
 | VTMP     | Virtual temperature                               | K             |
 | POT      | Potential temperature                             | K             |
 | EPOT     | Equivalent potential temperature                  | K             |
 | DPT      | Dew point temperature                             | K             |
 | DEPR     | Dew point depression (or deficit)                 | K             |
 | VIS      | Visibility                                        | m             |
 | WDIR     | Wind direction (from which blowing)               | deg true      |
 | WIND     | Wind speed                                        | m/s           |
 | UGRD     | u-component of wind                               | m/s           |
 | VGRD     | v-component of wind                               | m/s           |
 | VVEL     | Vertical velocity (pressure)                      | Pa/s          |
 | DZDT     | Vertical velocity (geometric)                     | m/s           |
 | ABSV     | Absolute vorticity                                | /s            |
 | ABSD     | Absolute divergence                               | /s            |
 | RELV     | Relative vorticity                                | /s            |
 | RELD     | Relative divergence                               | /s            |
 | SPFH     | Specific humidity                                 | kg/kg         |
 | RH       | Relative humidity                                 | %             |
 | MIXR     | Humidity mixing ratio                             | kg/kg         |
 | PWAT     | Precipitable water                                | kg/m2         |
 | VAPP     | Vapor pressure                                    | Pa            |
 | SATD     | Saturation deficit                                | Pa            |
 | EVP      | Evaporation                                       | kg/m2         |
 | CICE     | Cloud Ice                                         | kg/m2         |
 | PRATE    | Precipitation rate                                | kg/m2/s       |
 | APCP     | Total precipitation                               | kg/m2         |
 | WEASD    | Water equiv. of accum. snow depth                 | kg/m2         |
 | SNOD     | Snow depth                                        | m             |
 | MIXHT    | Mixed layer depth                                 | m             |
 | TTHDP    | Transient thermocline depth                       | m             |
 | TCDC     | Total cloud cover                                 | %             |
 | CDCON    | Convective cloud cover                            | %             |
 | LCDC     | Low cloud cover                                   | %             |
 | MCDC     | Medium cloud cover                                | %             |
 | HCDC     | High cloud cover                                  | %             |
 | CWAT     | Cloud water                                       | kg/m2         |
 | WTMP     | Water Temperature                                 | K             |
 | LAND     | Land cover (land=1, sea=0) (see note)             | proportion    |
 | SFCR     | Surface roughness                                 | m             |
 | ALBDO    | Albedo                                            | %             |
 | TSOIL    | Soil temperature                                  | K             |
 | SOILM    | Soil moisture content                             | kg/m2         |
 | VEG      | Vegetation                                        | %             |
 | SALTY    | Salinity                                          | kg/kg         |
 | DEN      | Density                                           | kg/m3         |
 | WATR     | Water runoff                                      | kg/m2         |
 | ICEC     | Ice cover (ice=1, no ice=0) (See Note)            | proportion    |
 | ICETK    | Ice thickness                                     | m             |
 | NSWRS    | Net short-wave radiation flux (surface)           | W/m2          |
 | NLWRS    | Net long wave radiation flux (surface)            | W/m2          |
 | NSWRT    | Net short-wave radiation flux (top of atmosphere) | W/m2          |
 | NLWRT    | Net long wave radiation flux (top of atmosphere)  | W/m2          |
 | LWAVR    | Long wave radiation flux                          | W/m2          |
 | SWAVR    | Short wave radiation flux                         | W/m2          |
 | BRTMP    | Brightness temperature                            | K             |
 | LHTFL    | Latent heat net flux                              | W/m2          |
 | SHTFL    | Sensible heat net flux                            | W/m2          |
 | LTNG     | Lightning                                         | non-dim       |


Select levels

| Level                                            |
| ------------------------------------------------ |
| entire atmosphere                                |
| cloud top                                        |
| surface                                          |
| 250 mb                                           |
| 300 mb                                           |
| 500 mb                                           |
| 700 mb                                           |
| 850 mb                                           |
| 925 mb                                           |
| 1000 mb                                          |
| mean sea level                                   |
| 2 m above ground                                 |
| 80 m above ground                                |
| 0 m underground                                  |
| 10 m above ground                                |
| top of atmosphere                                |

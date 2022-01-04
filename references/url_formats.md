# Model URL Structure

The purpose of this document is to understand how the various URL structures are organized at the different sources. 

> An idea, can Herbie help create a "map" of what files are available at each source?

---

# HRRR

HRRR is very clean (yeah, I added a little complexity when I created Pando).

```
https://noaa-hrrr-bdp-pds.s3.amazonaws.com/
https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/
https://storage.googleapis.com/high-resolution-rapid-refresh/
https://noaahrrr.blob.core.windows.net/hrrr/
    hrrr.20211103/
        conus/
            hrrr.t00z.wrfnatf00.grib2
            hrrr.t00z.wrfnatf00.grib2.idx
            hrrr.t00z.wrfprsf00.grib2
            hrrr.t00z.wrfprsf00.grib2.idx
            hrrr.t00z.wrfsfcf00.grib2
            hrrr.t00z.wrfsfcf00.grib2.idx
            hrrr.t00z.wrfsubhf00.grib2
            hrrr.t00z.wrfsubhf00.grib2.idx
        alaska/
            hrrr.t00z.wrfnatf00.ak.grib2
            hrrr.t00z.wrfnatf00.ak.grib2.idx
            hrrr.t00z.wrfprsf00.ak.grib2
            hrrr.t00z.wrfprsf00.ak.grib2.idx 
            hrrr.t00z.wrfsfcf00.ak.grib2
            hrrr.t00z.wrfsfcf00.ak.grib2.idx 
            hrrr.t00z.wrfsubhf00.ak.grib2
            hrrr.t00z.wrfsubhf00.ak.grib2.idx 

https://pando-rgw01.chpc.utah.edu/
https://pando-rgw02.chpc.utah.edu/
    hrrr/
        sfc/20211103/
            hrrr.t00z.wrfsfcf00.grib2
            hrrr.t00z.wrfsfcf00.grib2.idx
        prs/20211103/
            hrrr.t00z.wrfprsf00.grib2
            hrrr.t00z.wrfprsf00.grib2.idx
    hrrrak/
        sfc/20211103/
            hrrrak.t00z.wrfsfcf00.grib2
            hrrrak.t00z.wrfsfcf00.grib2.idx
```
## Summary

Start Date : 2014-07-30  
End Date: Current

- https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.20211103/conus/hrrr.t00z.wrfnatf00.grib2
- https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20211103/conus/hrrr.t00z.wrfnatf01.grib2
- https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.20140821/conus/hrrr.t00z.wrfnatf00.grib2
- https://noaahrrr.blob.core.windows.net/hrrr/hrrr.20211102/conus/hrrr.t00z.wrfnatf00.grib2
- https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20211103/hrrr.t00z.wrfsfcf00.grib2


# RAP

Much more complex; lots of model domain options, historical files are all over the place and incomplete.

```
https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/
https://noaa-rap-pds.s3.amazonaws.com/
https://storage.googleapis.com/rapid-refresh/
    rap.20211103/
        rap.t00z.awip32f00.grib2
        rap.t00z.awip32f00.grib2.idx
              *  awip32
              *  awp130bgrb
              *  awp130pgrb
              *  awp200
              *  awp236pgrb
              *  awp242
                 awp243
              *  awp252bgrb
              *  awp252pgrb
                 wrfmsl
                 wrfnat
              *  wrfprs             (*Has .idx file)
        
    rap_p.20211103/   # Only bufr stuff, right?
    rap_e.20211103/   # Only bufr stuff, right?

# Notice below that files in the historical directory replace .grb2 with .inv 
# instead of appending. This is not done for the recent directories.

https://www.ncei.noaa.gov/data/rapid-refresh/access/
    historical/
        analysis/202005/20200515/
            rap_130_20200515_0000_000.grb2
            rap_130_20200515_0000_000.inv
            rap_252_20200515_0000_000.grb2
            rap_252_20200515_0000_000.inv
            ruc2_252_20050101_0000_000.grb    # old RUC model is in GRIB1
            ruc2_252_20050101_0000_000.inv
        forecast/202005/20200517/
            rap_252_20200517_0000_000.grb2
            rap_252_20200517_0000_000.inv
            ruc2_236_20050101_1500_001.grb    # old RUC model is in GRIB1
            ruc2_236_20050101_1500_001.inv
            ruc_211_20050101_1500_003.grb
            ruc_211_20050101_1500_003.inv
    rap-130-13km/
        analysis/201205/20120531/
            rap_130_20120531_0200_000.grb2
            rap_130_20120531_0200_000.grb2.inv	
        forecast/202111/
            rap_130_202111_0000_000.grb2
            rap_130_202111_0000_000.grb2.inv
    rap-252-20km/
        analysis/201205/20120531
            rap_252_20120531_0300_000.grb2
            rap_252_20120531_0300_000.grb2.inv	
        forecast/202111/20211101/
            rap_252_20211101_0000_000.grb2
            rap_252_20211101_0000_000.grb2.inv
```

## Summary

**RAP on NOMADS**  
Start Date:  Yesterday  
End Date: Today

**RAP on Big Data Project**  
Start Date:  2021-02-22  
End Date: Current

**RAP at NCEI**  
Start Date: 2012-05-10  
End Date: two days ago or yesterday??

**RAP/RUC at NCEI Historical**  
Start Date: 2005-01   
End Date: 2020-05 

- https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.20211103/rap.t00z.awip32f00.grib2
- https://noaa-rap-pds.s3.amazonaws.com/rap.20211103/rap.t00z.awip32f00.grib2
- https://storage.googleapis.com/rapid-refresh/rap.20211103/rap.t00z.awip32f00.grib2
- https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/forecast/202005/20200517/rap_252_20200517_0000_000.grb2


> **NCEI data is messy and incomplete**   
>
> ---
> Herbie should look in the RAP forecast directory first, then the analysis directory (because the analysis files might also be in the forecast directory). Then proceed to look in the historical directory (let the user specify the default priority order in-line or in config file). But this only works for the 252-20km dataset (the 13-km forecasts are not archived).
>
> the parameter `self.IDX_SUFFIX` could instead be a list that contains the suffixes of the files to look for and loop over to find the index files
> ```
> self.IDX_SUFFIX = ['.grb.inv', '.inv', '.grib2.idx', '.idx']
> ```
> Use ".grib2.idx" as the default value if this parameter is not specified.



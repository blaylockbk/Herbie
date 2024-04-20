# 🤖 Rclone

If you need to download many full GRIB2 files from the cloud, I would suggest using [rclone](https://rclone.org/) instead of Herbie. I love rclone!

Rclone is a command-line program that does multi-threaded downloads between different cloud providers or to local disk. Below is a brief tutorial to help you get started.

[![](https://rclone.org/img/logo_on_light__horizontal_color.svg)](https://rclone.org/)

As part of NOAA's Open Data Dissemination program, the NEXRAD radar, GOES satellite, HRRR model, and many other dataset are publicly available via Amazon Web Services (AWS) and other cloud providers. You can use `rclone` to download these datasets. You can even use rclone to access personal OneDrive, Google Drive, Box, and other types of cloud storage.

## Install and setup

If you use conda, rclone is simply installed like this:

    conda install -c conda-forge rclone

Or, you can download from <https://rclone.org/downloads/>.

Now configure `rclone` to access **Amazon S3**. You can configure a new remote via the command line walk-through by running the command

    rclone config

- Select `n` for _new remote_ and name the remote anything you like, but use a name that will remind you it accesses the public Amazon S3 buckets. I named mine `publicAWS`.
- Set _Type of Storage_ as `Amazon S3 Compliant Storage Providers` (5)
- Set _Storage Provider_ as `Amazon Web Services S3` (1).
- Leave everything else blank (push enter for the remaining prompts).
- If it looks right, accept with `y` and exit the setup.

The configuration file is saved in in this location

```
~/.config/rclone.config
```

And this should look like this

```ini file="~/.config/rclone.config"
[publicAWS]
type = s3
provider = AWS
```

## CLI Usage

You can now use the remote you just configured to access NOAA's public buckets on Amazon Web Services S3. Below are the names of some of NOAA's public buckets.

| Data   | Bucket Name          |                                                                  |
| ------ | -------------------- | ---------------------------------------------------------------- |
| HRRR   | `noaa-hrrr-bdp-pds`  | [documentation](https://registry.opendata.aws/noaa-hrrr-pds/)    |
| GFS    | `noaa-gfs-bdp-pds`   | [documentation](https://registry.opendata.aws/noaa-gfs-bdp-pds/) |
| GEFS   | `noaa-gefs-pds`      | [documentation](https://registry.opendata.aws/noaa-gefs/)        |
| GOES16 | `noaa-goes16`        | [documentation](https://registry.opendata.aws/noaa-goes/)        |
| GOES17 | `noaa-goes17`        | [documentation](https://registry.opendata.aws/noaa-goes/)        |
| GOES18 | `noaa-goes18`        | [documentation](https://registry.opendata.aws/noaa-goes/)        |
| NEXRAD | `noaa-nexrad-level2` | [documentation](https://registry.opendata.aws/noaa-nexrad/)      |

> Note: **bdp-pds** stands for Big Data Program Public Data Set

You access the bucket contents by typing the command

```bash
rclone <command> <options> <remoteName>:<bucket>
```

Documentation for all the commands and options can be found on the [rclone](https://rclone.org/) website.

### List bucket directories

```bash
rclone lsd publicAWS:noaa-goes16/
```

### List bucket directories for specific folders

```bash
rclone lsd publicAWS:noaa-hrrr-bdp-pds/hrrr.20210101
```

### List files in bucket

```bash
rclone ls publicAWS:noaa-hrrr-bdp-pds/hrrr.20210101/conus
```

### Copy file or files to your local machine

```bash
rclone copy publicAWS:noaa-goes16/ABI-L2-MCMIPC/2018/283/00/OR_ABI-L2-MCMIPC-M3_G16_s20182830057203_e20182830059576_c20182830100076.nc ./
```

## Examples

### HRRR

For accessing HRRR from AWS and/or [Azure](https://planetarycomputer.microsoft.com/dataset/storage/noaa-hrrr), this should be in your `~/.config/rclone/rclone.conf` file:

```ini
[publicAWS]
type = s3
provider = AWS

[azure-hrrr]
type = azureblob
sas_url = https://noaahrrr.blob.core.windows.net/hrrr
```

Usage examples

```bash
# List HRRR buckets on AWS
rclone lsd publicAWS:noaa-hrrr-bdp-pds

# List HRRR blobs on Azure
rclone lsd azure-hrrr:hrrr
```

### ECMWF

For accessing ECMWF open data on AWS or Azure, this should be in your `~/.config/rclone/rclone.conf` file:

```ini
[publicAWS]
type = s3
provider = AWS

[azure-ecmwf]
type = azureblob
sas_url = https://ai4edataeuwest.blob.core.windows.net/ecmwf
```

Usage examples

```bash
# List ECMWF buckets on AWS
rclone lsd publicAWS:ecmwf-forecasts

# List ECMWF blobs on Azure
rclone lsd azure-ecmwf:ecmwf
```

Copy all `oper` and `scda` data from a certain day/hour to your local computer

```bash
rclone copy azure-ecmwf:ecmwf/20221213/ . --include "*-{oper,scda}-fc.{grib2,index}"
```

| Command Part                                 | Explanation                                                     |
| -------------------------------------------- | --------------------------------------------------------------- |
| `rclone`                                     | the rclone command                                              |
| `copy`                                       | copy data from A to B                                           |
| `azure-ecmwf:ecmwf/20221213/`                | The data source                                                 |
| `.`                                          | The location to download the dat (preserve directory structure) |
| `--include "*-{oper,scda}-fc.{grib2,index}"` | filter the files you want downloaded                            |

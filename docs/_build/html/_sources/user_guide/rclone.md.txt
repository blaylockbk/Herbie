# 🤖 Rclone

If you just need to download files from the cloud, I will direct you to [rclone](https://rclone.org/). I love rclone! Below is a brief tutorial to help you get started.


[![](https://rclone.org/img/logo_on_light__horizontal_color.svg)](https://rclone.org/)


As part of NOAA's Big Data Project, the NEXRAD radar, GOES satellite, HRRR model, and other dataset are publicly available via Amazon Web Services (AWS). You can use `rclone` to access these datasets and download. (You can even use rclone to access personal OneDrive, Google Drive, Box, and other types of cloud storage.)

# Install and Setup

## 1. Download and install `rclone` on your linux machine

Download from https://rclone.org/downloads/ or install with conda.

    conda install -c conda-forge rclone

## 2. Configure `rclone` to access **Amazon S3**
After `rclone` has been downloaded and installed, configure a remote by typing `rclone config`. Then type `n` for `new remote`.

Name the remote anything you like, but use a name that will remind you it accesses the public Amazon S3 buckets. I named mine `publicAWS`. 

Set _Type of Storage_ as `Amazon S3 Compliant Storage Providers`

Set _Storage Provider_ as `Amazon Web Services S3`.

Leave everything else blank (push enter for the remaining prompts).

The prompt will ask you if something like following is correct:

    [publicAWS]
    type = s3
    provider = AWS
    env_auth =
    access_key_id =
    secret_access_key =
    region =
    endpoint =
    location_constraint =
    acl =
    server_side_encryption =
    storage_class =

If it looks right, accept with `y` and exit the setup.

This configuration is saved in the `~/.config/rclone.config` file.

# CLI Usage

You will use the remote you just configured to access NOAA's public buckets on Amazon Web Services S3. Below are the names of some of NOAA's public buckets. 

| Data   | Bucket Name          |                                         |
| ------ | -------------------- | ---------------------------------------------------- |
| GOES16 | `noaa-goes16`        | [documentation](https://registry.opendata.aws/noaa-goes/)     |
| GOES17 | `noaa-goes17`        | [documentation](https://registry.opendata.aws/noaa-goes/)     |
| NEXRAD | `noaa-nexrad-level2` | [documentation](https://registry.opendata.aws/noaa-nexrad/)   |
| HRRR   | `noaa-hrrr-bdp-pds`  | [documentation](https://registry.opendata.aws/noaa-hrrr-pds/) |

> Note: **bdp-pds** stands for Big Data Program Public Data Set

You access the bucket contents by typing the command

    rclone <command> <options> <remoteName>:<bucket>
    
Documentation for all the commands and options can be found on the [rclone](https://rclone.org/) website.

List bucket directories

```bash
rclone lsd publicAWS:noaa-goes16/
```
List bucket directories for specific folders
```bash
rclone lsd publicAWS:noaa-hrrr-bdp-pds/hrrr.20210101
```
List files in bucket
```bash
rclone ls publicAWS:noaa-hrrr-bdp-pds/hrrr.20210101/conus
```

Copy file or files to your local machine

```bash
rclone copy publicAWS:noaa-goes16/ABI-L2-MCMIPC/2018/283/00/OR_ABI-L2-MCMIPC-M3_G16_s20182830057203_e20182830059576_c20182830100076.nc ./
```

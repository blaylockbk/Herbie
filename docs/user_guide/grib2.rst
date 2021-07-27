.. _GRIB2_FAQ:

What is GRIB2?
--------------
GRIB stands for "gridded binary" and is an international standard for meteorological data. There is an old standard GRIB, and a new standard GRIB2. In these documetns, when I refer to GRIB I really mean the new GRIB2 standard.

Yes, GRIB is notoriously difficult to work with and has a steep learning curve for those unfamiliar with the format. I won't discuss here the good, bad, and ugly of GRIB frankly because I'm not an expert and probably will say something wrong. However, even seasoned meteorologists complain about GRIB. Since complaining won't fix the problem, I choose to embrace it because, for now, NWP data is widely distributed as GRIB2.  

- `Wikipedia: GRIB <https://en.wikipedia.org/wiki/GRIB>`_

GRIB2 Tools
-----------

Command Line Tools
^^^^^^^^^^^^^^^^^^
There are two command-line tools for looking at GRIB file contents.

1. *wgrib2* is a product of NOAA and can be installed via conda-forge in your environment (linux only). | `wrgib2 documentation <https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/>`_ |
2. *grib_ls* is a product of ECMWF and is a dependency of cfgrib. This utility is included when you install cfgrib in your conda environment.

For a sample GRIB2 file with precipitation data, below is the output using both tools

.. code-block:: bash

   $ wgrib2 subset_20201214_hrrr.t00z.wrfsfcf12.grib2
   1:0:d=2020121400:APCP:surface:0-12 hour acc fcst:
   2:887244:d=2020121400:APCP:surface:11-12 hour acc fcst:

.. code-block:: bash

   $ grib_ls subset_20201214_hrrr.t00z.wrfsfcf12.grib2 
   subset_20201214_hrrr.t00z.wrfsfcf12.grib2
   edition      centre       date         dataType     gridType     typeOfLevel  level        stepRange    shortName    packingType  
   2            kwbc         20201214     fc           lambert      surface      0            0-12         tp           grid_complex_spatial_differencing 
   2            kwbc         20201214     fc           lambert      surface      0            11-12        tp           grid_complex_spatial_differencing 
   2 of 2 messages in subset_20201214_hrrr.t00z.wrfsfcf12.grib2

   2 of 2 total messages in 1 files

Python Tools
^^^^^^^^^^^^
There are two key python packages for reading GRIB2 files. Both can be installed via conda-forge.

- **pygrib** is what I started to learn and still use sometimes. | `Video Demo <https://youtu.be/yLoudFv3hAY>`_ |  `pygrib GitHub <https://github.com/jswhit/pygrib>`_ |
- **cfgrib** works well reading GRIB2 data as xarray datasets. Make sure you have the latest version (>0.9.8) |  `cfgrib GitHub <https://github.com/ecmwf/cfgrib>`_

How GRIB subsetting works
-------------------------
GRIB files are gridded binary. GRIB "messages" or "fields" are stacked on top of each other in a file. Each field contains data for one variable at a specific level across the gridded model domain. Because the file is made up of individual "messages," it is possible to download portions of GRIB2 file by retrieving just specific messages.

Herbie supports **subsetting GRIB2 files by GRIB message**, provided that an index (.idx) file exists. The index file tells us the beginning byte of each GRIB message. To download a subset, Herbie uses the cURL command which allows you to download a range of bytes from a file. By repeating the cURL command and appending the messages you a file, you can subset a full file on the remote server and download only the fields you need. Keep in mind that a GRIB message represents the variable over the full grid. It is only possible to subset the file by GRIB message and not by geographical region (i.e., you cannot do a regional subset). 

Why would you want to subset GRIB2 files? Well, GRIB files provided by operational forecast centers are usually very large because they can contain hundred of model output variables, and each variable is its own GRIB message. For example, native grid HRRR files can be ~700 MB each! That adds up quick if you need a lot of days and forecasts. Often, you only need some of the data in the file. The size of a single HRRR message is about 1 MB. If you subset the data as you download it, you will save a lot of disk space and improve download time.

.. figure:: ../_static/diagrams/GRIB2_file_cURL.png

   GRIB2 files are made up of messages or fields that can be extracted instead of downloading the full file.

The challenge to downloading parts of the full GRIB2 file finding the byte range for a variable you want. The beginning byte of each variable is given in the index, or .idx, file.

Partial downloads with cURL require a known byte range. The grbi2.idx ( sfc example , prs example) files are metadata text files that contain the beginning byte of each field in the file. Each grib2 file has a unique index file. To find the byte range for a variable, the above function searches for the line that contains the specified variable abbreviation and level.

.. image:: ../_static/diagrams/index_file_description.png

If an inventory file does not exists, one can be created using wgrib2. 

.. code-block::
    bash

    wgrib2 -s file.grib2 > file.grib2.idx

If you know the byte range of the variable you want (found from the .idx file), you can retrieve that single variable. The .idx> files share the same URL as the grib2, except with .idx> appended to the end. For example, from the .idx file for F00 valid at 0000 UTC 1 January 2018, we see that the byte range for TMP:2 m starts at 34884036 and ends at 36136433.

.. code-block:: bash
   
   curl -o 20180101_00zf00_2mTemp.grib2 --range 34884036-36136433 https://pando-rgw01.chpc.utah.edu/hrrr/sfc/20180101/hrrr.t00z.wrfsfcf00.grib2

After inspecting the downloaded file, you will see cURL has downloaded a valid GRIB2 file with only the 2 meter temperature variable.

You could repeat the steps for different byte ranges to get different variables and append the output to a file

curl --range ######-###### >> outFile.grib2

This method is similar to that used in Wesley Ebisuzaki's `Fast Downloading GRIB <https://www.cpc.ncep.noaa.gov/products/wesley/fast_downloading_grib.html>`_ script.

.. note:: 
    Regional subsetting is not possible with the methods. This would require some server-side processes. A useful alternative to the GRIB standard is the fairly new Zarr format, which makes subsetting by region possible. 


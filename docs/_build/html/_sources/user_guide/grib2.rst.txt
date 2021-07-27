.. _GRIB2_FAQ:

==============
What is GRIB2?
==============

**Subsetting these files by GRIB message** is also supported, provided that an index (.idx) file exists. GRIB files contain "messages" which define a grid of data for a particular variable. Data for each variable is stacked on top of each other. Instead of downloading full GRIB2 files, you may download a selections from a GRIB2 file based on GRIB message. This is enabled by the cURL command which allows you to download a range of bytes from a file. GRIB index files list the beginning byte for each GRIB field. Herbie searches these index file for the variables you want and performs the cURL command for each field. The returned data is a valid GRIB2 file that contains the whole grid for just the requested variable.

.. image:: _static/diagrams/GRIB2_file_cURL.png

.. image:: _static/diagrams/index_file_description.png
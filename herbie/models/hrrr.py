## Added by Brian Blaylock
## July 26, 2021

"""
A Herbie template for the HRRR model.

Because the file path to GRIB2 model data is predictable, we can
template the download URL for model output. Follow this template for
writing your own template file for any model with GRIB2 files available
via https.

Requirements
------------
1. Model must be available via https
2. Preferably, an .idx file should be available.
3. URL must be consistent across time and products.

Properties
----------
DESCRIPTION : str
    A description of the model. Give the full name and the
    domain, if relevant.
DETAILS : dict
    Some additional details about the model. Provide links
    to web documentation.
PRODUCTS : dict
    Models usually have different product types. The keys are
    used in building the GRIB2 source URL.
    ORDER MATTERS -- If product is None, then Herbie uses the first
    as default.
SOURCES : dict
    Build the URL for the GRIB2 file for different sources.
    The parameters are from arguments passed into the
    ``herbie.archive.Herbie()`` class.
    ORDER MATTERS -- If priority is None, then Herbie searches the
    sources in the order given here.
LOCALFILE : str
    The local file to save the model output. The file will be saved in
    ``save_dir/model/YYYYmmdd/localFile.grib2``
    It is sometimes necessary to add details to maintain unique
    filenames (e.g., rrfs needs to have the member number in LOCALFILE).
TODO
EXPECT_IDX_FILE : {'remote', 'local', 'none'}
    (Not implemented, but might be in the future)
    Where to expect the inventory index file, on the 'remote' server,
    on the 'local' disk, or 'none' for non-grib files.
    Default will be set to 'remote'
"""


class hrrr:
    def template(self):
        self.DESCRIPTION = "High-Resolution Rapid Refresh - CONUS"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
            "University of Utah HRRR archive": "http://hrrr.chpc.utah.edu/",
        }
        self.PRODUCTS = {
            "sfc": "2D surface level fields; 3-km resolution",
            "prs": "3D pressure level fields; 3-km resolution",
            "nat": "Native level fields; 3-km resolution",
            "subh": "Subhourly grids; 3-km resolution",
        }
        self.SOURCES = {
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "pando": f"https://pando-rgw01.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
        }
        self.EXPECT_IDX_FILE = 'remote'
        self.LOCALFILE = f"{self.get_remoteFileName}"


class hrrrak:
    def template(self):
        self.DESCRIPTION = "High-Resolution Rapid Refresh - Alaska"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr",
        }
        self.PRODUCTS = {
            "prs": "3D pressure level fields; 3-km resolution",
            "sfc": "2D surface level fields; 3-km resolution",
            "nat": "Native level fields; 3-km resolution",
            "subh": "Subhourly grids; 3-km resolution",
        }
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2",
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2",
            "pando": f"https://pando-rgw01.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2",
        }
        self.EXPECT_IDX_FILE = 'remote'
        self.LOCALFILE = f"{self.get_remoteFileName}"

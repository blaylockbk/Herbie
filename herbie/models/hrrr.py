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
1. Model GRIB2 file must be available via https
2. Preferably, an .idx file should be available.
3. URL must be consistent across time and products.

Properties
----------
DESCRIPTION : str
    A description of the model. Give the full name and the
    domain, if relevant. Just infor for the user.
DETAILS : dict
    Some additional details about the model. Provide links
    to web documentation. Just info for the user.
PRODUCTS : dict
    Models usually have different product types. The keys are
    used in building the GRIB2 source URL.
    ORDER MATTERS -- If product is None, then Herbie uses the first
    as default.
    *ONLY ONE IS USED (FIRST IS USED IF NOT SET)*
SOURCES : dict
    Build the URL for the GRIB2 file for different sources.
    The parameters are from arguments passed into the
    ``herbie.core.Herbie()`` class.
    ORDER MATTERS -- If priority is None, then Herbie searches the
    sources in the order given here.
    *LOOP THROUGH ALL SOURCES*
LOCALFILE : str
    The local file to save the model output. The file will be saved in
    ``save_dir/model/YYYYmmdd/localFile.grib2``
    It is sometimes necessary to add details to maintain unique
    filenames (e.g., rrfs needs to have the member number in LOCALFILE).
EXPECT_IDX_FILE : {None, "remote"}
    If None, Herbie knows not to expect an index file for this kind
    of file. (Perhaps the file is not a GRIB file.)
    If "remote", then Herbie will expect an index file on the remote
    location. This is the default value.


Optional
--------
IDX_SUFFIX : list
    Default value is ["grib.idx"], which is pretty standard.
    But for some, like RAP, the idx files are messy and could be a few
    different styles.
    self.IDX_SUFFIX = [".grb2.inv", ".inv", ".grb.inv"]
    *LOOP THROUGH ALL SUFFIXES TO FIND AN INDEX FILE*

IDX_STYLE : {'wgrib2', 'eccodes'}
    This defines how the index will be interpreted.
    - NCEP products use ``wgrib2`` to create index files.
    - ECMWF products use ``eccodes`` to create index files.
"""
__all__ = ["hrrr", "hrrrak"]

from datetime import datetime


class hrrr:
    """Template for High-Resolution Rapid Refresh model (HRRR)."""

    def template(self):
        # --------
        # Metadata
        self.DESCRIPTION = "High-Resolution Rapid Refresh - CONUS"
        self.IDX_SUFFIX = [".grib2.idx"]
        self.IDX_STYLE = "wgrib2"
        self.EXPECT_IDX_FILE = "remote"
        self.SOURCE_LINKS = {
            "aws": "",
            "google": "",
            "azure": "",
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
            "pando": "http://hrrr.chpc.utah.edu/",
        }

        # ----------
        # Validation

        # HRRR produces output every hour, so we don't really need to
        # check that the hour is correct. But let's to it just to
        # demonstrate (this is an important step for models that run
        # every 6 hours.)
        _hours = range(0, 24)
        if self.date.hour not in _hours:
            raise ValueError(f"Request date's hour must be one of {list(_hours)}")

        # HRRR produces different output products. If not given, the
        # default will be the 'sfc' product.
        _products = {
            "sfc": "2D surface level fields; 3-km resolution",
            "prs": "3D pressure level fields; 3-km resolution",
            "nat": "Native level fields; 3-km resolution",
            "subh": "Subhourly grids; 3-km resolution",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(f"`product` must be one of {list(_products)}")

        # -----------------
        # Build Source URLs

        post_root = f"hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2"

        self.SOURCES = {
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{post_root}",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/{post_root}",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/{post_root}",
        }

        # Pando HRRR archive has slightly different naming pattern
        post_root_pando = f"{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2"
        self.SOURCES |= {
            "pando": f"https://pando-rgw01.chpc.utah.edu/{post_root_pando}",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{post_root_pando}",
        }

        if self.product == "subh" and self.date <= datetime(2018, 9, 16):
            # Fix Issue #34 (not pretty, but gets the job done for now)
            # The subhourly filenames are different for older files.
            # prepend the self.SOURCES dict with the old filename format.
            # This requires an additional arg for `fxx_subh` when calling Herbie
            self.SOURCES = {
                "aws_old_subh": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.{self.date:%Y%m%d}/conus/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}{self.fxx_subh:02d}.grib2"
            } | self.SOURCES

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
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"

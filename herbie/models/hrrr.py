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

----------------
Part 1: Metadata
----------------
DESCRIPTION : str
    A description of the model. Give the full name and the
    domain, if relevant.
SOURCE_INFO : dict
    Links to web documentation for each of the model sources.
    Should match the sources listed in PRODUCTS.

-------------------
Part 2: Index Files
-------------------
IDX_SUFFIX : list of str
    If not given, Herbie's default is ["grib.idx"], which is pretty standard.
    But for some, like RAP, the idx files are messy and could be a few
    different styles.
    *Herbie will loop through all suffix styles in order given.*
    self.IDX_SUFFIX = [".grb2.inv", ".inv", ".grb.inv"]
IDX_STYLE : {'wgrib2', 'eccodes'}
    This defines how the index will be interpreted.
    - NCEP products use ``wgrib2`` to create index files.
    - ECMWF products use ``eccodes`` to create index files.
EXPECT_IDX_FILE : {None, "remote"}
    If None, Herbie knows not to expect an index file for this kind
    of file. (Perhaps the file is not a GRIB file.)
    If "remote", then Herbie will expect an index file on the remote
    location. This is the default value.


------------------
Part 3: Validation
------------------

PRODUCTS : dict
    Models usually have different product types. The keys are
    used in building the GRIB2 source URL.
    If `product` is not given or is None, then Herbie uses the first
    as default.

-------------------------
Part 4: Build Source URLs
-------------------------

SOURCES : dict
    Build the URL for the GRIB2 file for different sources using
    values set in the Herbie class.
    ORDER MATTERS; If `priority` is None, then Herbie searches the
    sources in the order given here.
LOCALFILE : str
    The local file to save the model output. The file will be saved in
    ``save_dir/model/YYYYmmdd/localFile.grib2``
    It is sometimes necessary to add details to maintain unique
    filenames (e.g., rrfs needs to have the member number in LOCALFILE).
"""

__all__ = ["hrrr", "hrrrak"]

from datetime import datetime


class hrrr:
    """Template for CONUS High-Resolution Rapid Refresh model (HRRR)."""

    def template(self):
        """Metadata, Validation, and Source URLs."""
        # --------
        # Metadata

        self.DESCRIPTION = "NOAA High-Resolution Rapid Refresh - CONUS"
        self.SOURCE_INFO = {
            "aws": "",
            "google": "",
            "azure": "",
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr/",
            "pando": "http://hrrr.chpc.utah.edu/",
        }

        # -----------
        # Index Files

        self.IDX_SUFFIX = [".grib2.idx"]
        self.IDX_STYLE = "wgrib2"

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
            "sfc": "2D surface level fields; 3-km grid",
            "prs": "3D pressure level fields; 3-km grid",
            "nat": "Native level fields; 3-km grid",
            "subh": "Subhourly grids; 3-km grid",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(
                f"`product` must be one of... \n{"\n".join(f" | '{key}' - {value}" for key, value in _products.items())}"
            )

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
    """Template for Alaska High-Resolution Rapid Refresh model (HRRR-AK)."""

    def template(self):
        """Metadata, Validation, and Source URLs."""
        # --------
        # Metadata

        self.DESCRIPTION = "NOAA High-Resolution Rapid Refresh - Alaska"
        self.SOURCE_INFO = {
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/hrrr",
        }

        # -----------
        # Index Files

        self.IDX_SUFFIX = [".grib2.idx"]
        self.IDX_STYLE = "wgrib2"
        self.EXPECT_IDX_FILE = "remote"

        # ----------
        # Validation

        # HRRR-Alaska produces output every 3 hours.
        _hours = range(0, 24, 3)
        if self.date.hour not in _hours:
            raise ValueError(f"Request date's hour must be one of {list(_hours)}")

        _products = {
            "prs": "3D pressure level fields; 3-km grid",
            "sfc": "2D surface level fields; 3-km grid",
            "nat": "Native level fields; 3-km grid",
            "subh": "Subhourly grids; 3-km grid",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(
                f"`product` must be one of... \n{"\n".join(f" | '{key}' - {value}" for key, value in _products.items())}"
            )

        # -----------------
        # Build Source URLs

        post_root = f"hrrr.{self.date:%Y%m%d}/alaska/hrrr.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.ak.grib2"

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hrrr/prod/{post_root}",
            "aws": f"https://noaa-hrrr-bdp-pds.s3.amazonaws.com/{post_root}",
            "google": f"https://storage.googleapis.com/high-resolution-rapid-refresh/{post_root}",
            "azure": f"https://noaahrrr.blob.core.windows.net/hrrr/{post_root}",
        }

        # Pando HRRR-Alask archive has slightly different naming pattern
        post_root_pando = f"{self.model}/{self.product}/{self.date:%Y%m%d}/{self.model}.t{self.date:%H}z.wrf{self.product}f{self.fxx:02d}.grib2"
        self.SOURCES |= {
            "pando": f"https://pando-rgw01.chpc.utah.edu/{post_root_pando}",
            "pando2": f"https://pando-rgw02.chpc.utah.edu/{post_root_pando}",
        }

        self.LOCALFILE = f"{self.get_remoteFileName}"

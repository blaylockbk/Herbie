## Added by Brian Blaylock
## July 26, 2021

from datetime import datetime


class gdas:
    """Template for Global Data Assimilation System."""

    def template(self):
        """Metadata, Validation, and Source URLs."""
        self.DESCRIPTION = "NOAA Global Data Assimilation System"
        self.SOURCE_INFO = {
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GDAS",
            "google": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs?q=search&referrer=search&project=python-232920",
            "azure": "https://github.com/microsoft/AIforEarthDatasets#noaa-global-forecast-system-gfs",
            "aws": "https://registry.opendata.aws/noaa-gfs-bdp-pds",
        }

        self.IDX_SUFFIX = [".idx"]

        _grids = ["0p25", "1p00"]
        if not hasattr(self, "grid") or self.grid is None:
            self.grid = _grids[0]
        elif self.grid not in set(_grids):
            raise ValueError(f"`grid` must be one of {_grids}")

        post_root = f"gdas.{self.date:%Y%m%d/%H}/atmos/gdas.t{self.date:%H}z.pgrb2.{self.grid}.f{self.fxx:03d}"

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{post_root}",
        }

        # TODO: What is the right date for the older GDAS format?
        # TODO: This is just a placeholder
        post_root_old = f"gdas.{self.date:%Y%m%d/%H}/gdas.t{self.date:%H}z.{self.product}.f{self.fxx:03d}"
        if self.date <= datetime(2018, 9, 16):
            self.SOURCES = {
                "aws-old": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root_old}",
            } | self.SOURCES

        self.LOCALFILE = f"{self.get_remoteFileName}"


class gfs:
    """Template for Global Forecast System."""

    def template(self):
        """Metadata, validate, URL tempalte."""
        self.DESCRIPTION = "NOAA Global Forecast System"
        self.SOURCE_INFO = {
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/gfs",
            "google": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs?q=search&referrer=search&project=python-232920",
            "azure": "https://github.com/microsoft/AIforEarthDatasets#noaa-global-forecast-system-gfs",
            "aws": "https://registry.opendata.aws/noaa-gfs-bdp-pds",
        }

        self.IDX_SUFFIX = [".idx"]

        _grids = ["0p25", "0p50", "1p00"]
        if not hasattr(self, "grid") or self.grid is None:
            self.grid = _grids[0]
        elif self.grid not in set(_grids):
            raise ValueError(f"`grid` must be one of {_grids}")

        _products = {
            "pgrb2": "common fields",
            "pgrb2b": "uncommon fields",
            "pgrb2full": "combined grids (`grid` must be '0p50'",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(
                f"`product` must be one of... \n{"\n".join(f" | '{key}' - {value}" for key, value in _products.items())}"
            )

        post_root = f"gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.{self.grid}.f{self.fxx:03d}"

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "aws-old": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.{self.date:%Y%m%d/%H}/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{post_root}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gfs_wave:
    """Tempalte for GFS wave products."""

    def template(self):
        """Metadata, validate, template."""
        self.DESCRIPTION = "NOAA Global Forecast System - Wave Products"
        self.SOURCE_INFO = {
            "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GFSwave",
        }

        _grids = ["0p16", "0p25", "9km"]
        if not hasattr(self, "grid") or self.grid is None:
            self.grid = _grids[0]
        elif self.grid not in set(_grids):
            raise ValueError(f"`grid` must be one of {_grids}")

        self.PRODUCTS = {
            "arctic": "Arctic; (`grid` must be '9km'",
            "atlocn": "North Atlantic",
            "epacif": "Eastern Pacific",
            "global": "Global",
            "gsouth": "Global South",
            "wcoast": "West Coast",
        }

        post_root = f"gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.{self.grid}.f{self.fxx:03d}.grib2"

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/gfs.{self.date:%Y%m%d/%H}/wave/gridder/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaahrrr.blob.core.windows.net/gfs/{post_root}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"

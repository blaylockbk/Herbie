"""Herbie template for GFS products."""

from datetime import datetime


class gfs:
    """Global Forecast System Atmosphere Products."""

    def template(self):
        self.DESCRIPTION = "Global Forecast System"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/gfs",
            "google cloud platform": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs?q=search&referrer=search&project=python-232920",
            "azure document": "https://github.com/microsoft/AIforEarthDatasets#noaa-global-forecast-system-gfs",
            "aws document": "https://registry.opendata.aws/noaa-gfs-bdp-pds",
        }
        self.PRODUCTS = {
            "pgrb2.0p25": "common fields, 0.25 degree resolution",
            "pgrb2.0p50": "common fields, 0.50 degree resolution",
            "pgrb2.1p00": "common fields, 1.00 degree resolution",
            "pgrb2b.0p25": "uncommon fields, 0.25 degree resolution",
            "pgrb2b.0p50": "uncommon fields, 0.50 degree resolution",
            "pgrb2b.1p00": "uncommon fields, 1.00 degree resolution",
            "pgrb2full.0p50": "combined grids of 0.50 resolution",
            "sfluxgrb": "surface flux fields, T1534 Semi-Lagrangian grid",
            "goesimpgrb2.0p25": ", 0.50 degree resolution",
        }

        if self.date < datetime(2021, 3, 23):
            post_root = f"gfs.{self.date:%Y%m%d/%H}/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}"
        else:
            # GFS update version 16.0
            # https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/implementations.php
            post_root = f"gfs.{self.date:%Y%m%d/%H}/atmos/gfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}"

        if self.product == "sfluxgrb":
            post_root = post_root.replace("sfluxgrb.", "sfluxgrb")

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{post_root}",
        }
        self.IDX_SUFFIX = [".idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gfs_wave:
    """
    Global Forecast System Wave Products.

    Wave products were made available with the GFS v16.0 upgrade on
    March 22, 2021.
    https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/implementations.php
    """

    def template(self):
        self.DESCRIPTION = "Global Forecast System - Wave Products"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GFSwave",
        }
        self.PRODUCTS = {
            "arctic.9km": "Arctic; 9-km resolution",
            "atlocn.0p16": "North Atlantic 0.16 deg resolution",
            "epacif.0p16": "Eastern Pacific; .16 deg resolution",
            "global.0p16": "Global; 0.16 deg resolution",
            "global.0p25": "Global; 0.25 deg resolution",
            "gsouth.0p25": "Global South; 0.25 deg resolution",
            "wcoast.0p16": "West Coast; 0.16 deg resolution",
        }

        post_root = f"gfs.{self.date:%Y%m%d/%H}/wave/gridded/gfswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2"

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaahrrr.blob.core.windows.net/gfs/{post_root}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gdas:
    """Global Data Assimilation System."""

    def template(self):
        self.DESCRIPTION = "Global Data Assimilation System"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GDAS",
            "google cloud platform": "https://console.cloud.google.com/marketplace/product/noaa-public/gfs?q=search&referrer=search&project=python-232920",
            "azure document": "https://github.com/microsoft/AIforEarthDatasets#noaa-global-forecast-system-gfs",
            "aws document": "https://registry.opendata.aws/noaa-gfs-bdp-pds",
        }
        self.PRODUCTS = {
            "pgrb2.0p25": "common fields, 0.25 degree resolution",
            "pgrb2.1p00": "common fields, 1.00 degree resolution",
            "sfluxgrb": "surface flux fields, T1534 Semi-Lagrangian grid",
        }

        if self.date < datetime(2021, 3, 23):
            post_root = f"gdas.{self.date:%Y%m%d/%H}/gdas.t{self.date:%H}z.{self.product}.f{self.fxx:03d}"
        else:
            # GFS update version 16.0
            # https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs/implementations.php
            post_root = f"gdas.{self.date:%Y%m%d/%H}/atmos/gdas.t{self.date:%H}z.{self.product}.f{self.fxx:03d}"

        if self.product == "sfluxgrb":
            post_root = post_root.replace("sfluxgrb.", "sfluxgrb")

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "aws-old": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaagfs.blob.core.windows.net/gfs/{post_root}",
        }
        self.IDX_SUFFIX = [".idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gdas_wave:
    def template(self):
        self.DESCRIPTION = "Global Data Assimilation System - Wave Products"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/gfs/#GFSwave",
        }
        self.PRODUCTS = {
            "arctic.9km": "Arctic; 9-km resolution",
            "atlocn.0p16": "North Atlantic 0.16 deg resolution",
            "epacif.0p16": "Eastern Pacific; .16 deg resolution",
            "global.0p16": "Global; 0.16 deg resolution",
            "global.0p25": "Global; 0.25 deg resolution",
            "gsouth.0p25": "Global South; 0.25 deg resolution",
            "wcoast.0p16": "West Coast; 0.16 deg resolution",
        }

        post_root = f"gdas.{self.date:%Y%m%d/%H}/wave/gridded/gdaswave.t{self.date:%H}z.{self.product}.f{self.fxx:03d}.grib2"

        self.SOURCES = {
            "aws": f"https://noaa-gfs-bdp-pds.s3.amazonaws.com/{post_root}",
            "ftpprd": f"https://ftpprd.ncep.noaa.gov/data/nccf/com/gfs/prod/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/{post_root}",
            "google": f"https://storage.googleapis.com/global-forecast-system/{post_root}",
            "azure": f"https://noaahrrr.blob.core.windows.net/gfs/{post_root}",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class graphcast:
    """GraphCast Global Forecast System."""

    def template(self):
        self.DESCRIPTION = "GraphCast Global Forecast System (EXPERIMENTAL)"
        self.DETAILS = {
            "aws document": "https://registry.opendata.aws/noaa-nws-graphcastgfs-pds/",
        }
        self.PRODUCTS = {
            "pgrb2.0p25": "common fields, 0.25 degree resolution",
        }
        self.SOURCES = {
            "aws": f"https://noaa-nws-graphcastgfs-pds.s3.amazonaws.com/graphcastgfs.{self.date:%Y%m%d/%H}/forecasts_13_levels/graphcastgfs.t{self.date:%H}z.{self.product}.f{self.fxx:03d}",
        }
        self.IDX_SUFFIX = [".idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

## Added by Brian Blaylock
## July 26, 2021


class rap:
    def template(self):
        self.DESCRIPTION = "Rapid Refresh"
        self.DETAILS = {
            "nomads product description": "https://www.nco.ncep.noaa.gov/pmb/products/rap",
        }
        self.PRODUCTS = {
            "awp130pgrb": "CONUS Pressure levels; 13-km resolution",
            "awp252pgrb": "CONUS Pressure levels; 20-km resolution",
            "awp236pgrb": "CONUS Pressure levels; 40-km resolution",
            "awp130bgrb": "CONUS Native levels; 13-km resolution",
            "awp252bgrb": "CONUS Native levels; 20-km resolution",
            "wrfprs": "Full domain Pressure Levels; 13-km",
            "wrfnat": "Full domain Native Levels; 13-km",
            "awip32": "NOAMHI - High-Resolution North American Master Grid; 32-km resolution",
            "awp242": "Alaska Quadruple Resolution Pressure levels; 11-km resolution",
            "awp200": "Puerto Rico Pressure levels; 16-km resolution",
            "awp243": "Eastern North America Pressure levels, 0.4 degree resolution",
            "wrfmsl": "WRFMSL; 13-km resolution",
        }
        self.SOURCES = {
            "aws": f"https://noaa-rap-pds.s3.amazonaws.com/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2",
            "google": f"https://storage.googleapis.com/rapid-refresh/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2",
            "azure": f"https://noaarap.blob.core.windows.net/rap/rap.{self.date:%Y%m%d}/rap.t{self.date:%H}z.{self.product}f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rap_ncei:
    """
    The RAP record at NCEI is very different than other sources.

    This isn't implemented super well.
    """

    def template(self):
        self.DESCRIPTION = "Rapid Refresh"
        self.DETAILS = {
            "nomads product description": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
        }
        self.PRODUCTS = {
            "historical/analysis": "RAP 13 km",
            "rap-130-13km/analysis": "RAP 13 km",  # longer archive
            "rap-130-13km/forecast": "RAP 13 km",  # very short archive
            "rap-252-20km/analysis": "RAP 20 km",
            "rap-252-20km/forecast": "RAP 20 km",
        }
        self.SOURCES = {
            "ncei": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{self.product}/{self.date:%Y%m/%Y%m%d}/rap_130_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
        }
        self.IDX_SUFFIX = ".inv"  # it is not .idx
        self.LOCALFILE = f"{self.get_remoteFileName}"

## Added by Brian Blaylock
## July 26, 2021
__all__ = ["rap", "rap_historical", "rap_ncei"]


class rap:
    """
    For NOMADS and Big Data Program RAP archive
    """

    def template(self):
        self.DESCRIPTION = "Rapid Refresh (RAP) from NOMADS and Big Data Program"
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


########################################################################
# The RAP record at NCEI is very different than the Big Data Program.
# Files are separated into historical/, rap-130-13km/, rap-252-20km/,
# analysis/, and forecast/ directories. These are inconsistent in years
# that are archived and have incomplete archived datetime groups.
# In a nutshell, NCEI's archive is very messy. Why anyone would want to
# use historical RAP is beyond me. Because the NCEI archive is so messy,
# Herbie may not be configured to find all possible file names in each
# year.
########################################################################

# TODO: Set LOCALFILE name to match modern filename structure.


class rap_historical:
    """
    The RAP and RUC historical record at NCEI. (files older than 2020)

    Grid 130 = 13 km
    Grid 252 = 20 km
    Grid 236 = ?? km
    Grid 211 = ?? km
    """

    def template(self):
        self.DESCRIPTION = "Rapid Refresh - NCEI Historical"
        self.DETAILS = {
            "nomads product description": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
        }
        self.PRODUCTS = {
            "analysis": "RAP",
            "forecast": "RAP",
        }
        self.SOURCES = {
            "rap_130": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/rap_130_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
            "rap_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/rap_252_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
            "ruc_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/ruc2_252_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb",
            "ruc_anl_252": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/ruc2anl_252_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb",
            "ruc_236": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/ruc2_236_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb",
            "ruc_211": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{self.product}/{self.date:%Y%m/%Y%m%d}/ruc_211_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb",
        }
        self.IDX_SUFFIX = [".inv", ".grb2.inv", "grb.inv"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class rap_ncei:
    """
    The RAP record at NCEI.

    Analysis: longer archive; May 2012 through a few days ago
    Forecast: short archive; 2021 through a few days ago
    """

    def template(self):
        self.DESCRIPTION = "Rapid Refresh 13 km - NCEI"
        self.DETAILS = {
            "nomads product description": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
        }
        self.PRODUCTS = {
            "rap-130-13km": "RAP 13 km",
            "rap-252-20km": "RAP 20 km",
        }
        # Well, it's either loop through the two sources and look for
        # files or create a separate class. I elected to just loop
        # through different URL's. Might not be the fastest, but it'll
        # work. The user can always specify the priority order.
        self.SOURCES = {
            "ncei_13km_analysis": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{self.product}/analysis/{self.date:%Y%m/%Y%m%d}/rap_130_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
            "ncei_13km_forecast": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{self.product}/forecast/{self.date:%Y%m/%Y%m%d}/rap_130_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
            "ncei_20km_analysis": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{self.product}/analysis/{self.date:%Y%m/%Y%m%d}/rap_252_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
            "ncei_20km_forecast": f"https://www.ncei.noaa.gov/data/rapid-refresh/access/{self.product}/forecast/{self.date:%Y%m/%Y%m%d}/rap_252_{self.date:%Y%m%d_%H%M}_{self.fxx:03d}.grb2",
        }
        self.IDX_SUFFIX = [".grb2.inv", ".inv", ".grb.inv"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

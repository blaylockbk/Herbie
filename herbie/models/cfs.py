## Added by Brian Blaylock
## May 29, 2023

"""
A Herbie template for the CFS (Climate Forecast System).
"""


class cfs_monthly:
    def template(self):
        self.DESCRIPTION = "Climate Forecast System; Monthly Means"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/cfs/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-cfs/",
            "Microsoft Azure": "https://planetarycomputer.microsoft.com/dataset/storage/noaa-cfs",
        }
        self.PRODUCTS = {
            "flxf": "CFS Surface, Radiative Fluxes",
            "pgbf": "CFS 3D Pressure Level, 1 degree resolution",
            "ocnh": "CFS 3D Ocean Data, 0.5 degree resolution",
            "ocnf": "CFS 3D Ocean Data, 1.0 degree resolution",
            "ipvf": "CFS 3D Isentropitc Level, 1.0 degree resolution",
        }

        try:
            self.member
        except NameError:
            print(
                "'member' is not defined. Please set 'member=1` for monthly data for the 6, 12, and 18 UTC cycles, but may be 1, 2, 3, or 4 for the 0 UTC cycle."
            )

        try:
            self.YYYYMM
        except NameError:
            print(
                "'YYYYMM' is not defined. Please specify the 4-digit year and 2-digit month you want forcast data from."
            )

        try:
            self.hour
        except NameError:
            print(
                "'hour' is not defined. Please set `hour` to one of {0, 6, 12, 18} or set to None for daily average."
            )

        if self.hour is None:
            # Daily average
            PATH = f"/cfs.{self.date:%Y%m%d/%H}/monthly_grib_{self.member:02d}/{self.product}.{self.member:02d}.{self.date:%Y%m%d%H}.{self.YYYYMM}.avrg.grib.grb2"
        else:
            PATH = f"/cfs.{self.date:%Y%m%d/%H}/monthly_grib_{self.member:02d}/{self.product}.{self.member:02d}.{self.date:%Y%m%d%H}.{self.YYYYMM}.avrg.grib.{self.hour:02d}Z.grb2"

        self.SOURCES = {
            "aws": f"https://noaa-cfs-pds.s3.amazonaws.com/{PATH}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{PATH}",
            # "azure": f"https://noaacfs.blob.core.windows.net/cfs/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

## Added by Brian Blaylock
## May 29, 2023

"""A Herbie template for the CFS (Climate Forecast System).

Details at https://cfs.ncep.noaa.gov/
"""

from pandas import to_datetime

import warnings


class cfs_monthly:
    def template(self):
        warnings.warn(
            "Herbie's CFS templates are and subject to major changes. PRs are welcome to improve it."
        )

        self.DESCRIPTION = "Climate Forecast System; Monthly Means"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/cfs/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-cfs/",
            "Microsoft Azure": "https://planetarycomputer.microsoft.com/dataset/storage/noaa-cfs",
            "NCEI": "https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system",
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
            post_root = f"cfs.{self.date:%Y%m%d/%H}/monthly_grib_{self.member:02d}/{self.product}.{self.member:02d}.{self.date:%Y%m%d%H}.{self.YYYYMM}.avrg.grib.grb2"
        else:
            post_root = f"cfs.{self.date:%Y%m%d/%H}/monthly_grib_{self.member:02d}/{self.product}.{self.member:02d}.{self.date:%Y%m%d%H}.{self.YYYYMM}.avrg.grib.{self.hour:02d}Z.grb2"

        self.SOURCES = {
            "aws": f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}",
            # "azure": f"https://noaacfs.blob.core.windows.net/cfs/{post_root}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class cfs_6_hourly:
    def template(self):
        warnings.warn(
            "Herbie's CFS templates are and subject to major changes. PRs are welcome to improve it."
        )
        self.DESCRIPTION = "Climate Forecast System; 6 hourly"
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
            self.forecast = to_datetime(self.forecast)
        except NameError:
            print(
                "'forecast' is not defined. Please set `set` to the forecast datetime."
            )

        post_root = f"cfs.{self.date:%Y%m%d/%H}/6hrly_grib_{self.member:02d}/{self.product}{self.forecast:%Y%m%d%H}.{self.member:02d}.{self.date:%Y%m%d%H}.grb2"

        self.SOURCES = {
            "aws": f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}",
            # "azure": f"https://noaacfs.blob.core.windows.net/cfs/{post_root}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class cfs_time_series:
    def template(self):
        warnings.warn(
            "Herbie's CFS templates are and subject to major changes. PRs are welcome to improve it."
        )
        self.DESCRIPTION = "Climate Forecast System; Time Series"
        self.DETAILS = {
            "NOMADS product description": "https://www.nco.ncep.noaa.gov/pmb/products/cfs/",
            "Amazon Open Data": "https://registry.opendata.aws/noaa-cfs/",
            "Microsoft Azure": "https://planetarycomputer.microsoft.com/dataset/storage/noaa-cfs",
        }
        # For reference:
        # https://www.nco.ncep.noaa.gov/pmb/products/cfs/#DAILY
        self.PRODUCTS = {
            # -----------------------
            # 3-D Pressure Level Data
            # -----------------------
            # Wind
            "wnd10m": "Wind u and v at 10 m",
            "wnd1000": "Wind u and v at 1000 hPa",
            "wnd925": "Wind u and v at 925 hPa",
            "wnd850": "Wind u and v at 850 hPa",
            "wnd500": "Wind u and v at 500 hPa",
            "wnd700": "Wind u and v at 700 hPa",
            "wnd250": "Wind u and v at 250 hPa",
            "wnd200": "Wind u and v at 200 hPa",
            "wndstrs": "Stress at surface",
            # Pressure
            "prmsl": "Pressure Reduced to MSL",
            "pressfc": "Surface Pressure",
            # Geopotential Height
            "z1000": "GeoPotential Height at 1000 hPa",
            "z850": "GeoPotential Height at 850 hPa",
            "z700": "GeoPotential Height at 700 hPa",
            "z500": "GeoPotential Height at 500 hPa",
            "z200": "GeoPotential Height at 200 hPa",
            # Temperature
            "tmpsfc": "Temperature at the Surface",
            "tmp2m": "Temperature at 2 m",
            "tmin": "Minimum Temperature at 2 m",
            "tmax": "Maximum Temperature at 2 m",
            "t1000": "Temperature at 1000 hPa",
            "t850": "Temperature at 850 hPa",
            "t700": "Temperature at 700 hPa",
            "t500": "Temperature at 500 hPa",
            "t250": "Temperature at 250 hPa",
            "t200": "Temperature at 200 hPa",
            "t50": "Temperature at 50 hPa",
            "t2": "Temperature at 2 hPa",
            "tmphy1": "Temperature at hybrid level 1",
            # Specific Humidity
            "q2m": "Specific Humidity at 2 m",
            "q925": "Specific Humidity at 925 hPa",
            "q850": "Specific Humidity at 850 hPa",
            "q700": "Specific Humidity at 700 hPa",
            "q500": "Specific Humidity at 500 hPa",
            # Velocity Potential
            "chi850": "Velocity Potential at 850 hPa",
            "chi200": "Velocity Potential at 200 hPa",
            # Radiation
            "dlwsfc": "Downward Longwave Radiation at the Surface",
            "dswsfc": "Downward Shortwave Radiation at the Surface",
            "ulwsfc": "Upward Longwave Radiation at the Surface",
            "uswsfc": "Upward Shortwave Radiation at the Surface",
            "ulwtoa": "Upward Longwave Radiation at the Top of the Atmosphere",
            "uswtoa": "Upward Shortwave Radiation at the Top of the Atmosphere",
            "gflux": "Ground Heat Flux",
            # Heat Flux
            "lhtfl": "Latent Heat Net Flux at the Surface",
            "shtfl": "Sensible Heat Net Flux at the Surface",
            # Other
            "cprat": "Convective Precipitation Rate",
            "csdlf": "Clear Sky Downward Longwave Flux",
            "csdsf": "Clear Sky Downward Solar Flux",
            "csusf": "Clear Sky Upward Solar Flux",
            "icecon": "Surface Ice Cover",
            "icethk": "Surface Ice Thickness",
            "ipv450": "Isentropic Potential Vorticity at 450 K",
            "ipv550": "Isentropic Potential Vorticity at 550 K",
            "ipv650": "Isentropic Potential Vorticity at 650 K",
            "nddsf": "Near IR Diffuse Downward Solar Flux",
            "tcdcclm": "Total Cloud Cover",
            "prate": "Total Precipitation Rate",
            "psi200": "Stream Function at 200 hPa",
            "psi850": "Stream Function at 850 hPa",
            "pwat": "Precipitable Water",
            "runoff": "Surface Runoff",
            "snohf": "Snowfall Rate Water Equivalent",
            "soilm1": "Vol. Soil Moisture Content, 0-10 cm Below Ground",
            "soilm2": "Vol. Soil Moisture Content, 10-40 cm Below Ground",
            "soilm3": "Vol. Soil Moisture Content, 40-100 cm Below Ground",
            "soilm4": "Vol. Soil Moisture Content, 100-200 cm Below Ground",
            "soilt1": "Soil Temperature, 0-0.1 m Below Ground",
            "vddsf": "Visible Diffuse Downward Solar Flux",
            "vvel500": "Vertical Velocity at 500 hPa",
            "weasd": "Water Equivalent of Accumulated Snow Depth",
            # --------------
            # 3-D Ocean Data
            # --------------
            # CFS Ocean Height
            "ocnmld": "Mixed Layer Depth",
            "ocnslh": "Sea Level Height",
            # CFS Ocean Depth of Isotherm
            "ocnsild": "Surface Isothermal Layer Depth",
            "ocndt2.5c": "Isothermal Layer Depth 2.5 Celsius",
            "ocndt5c": "Isothermal Layer Depth 5 Celsius",
            "ocndt10c": "Isothermal Layer Depth 10 Celsius",
            "ocndt15c": "Isothermal Layer Depth 15 Celsius",
            "ocndt20c": "Isothermal Layer Depth 20 Celsius",
            "ocndt25c": "Isothermal Layer Depth 25 Celsius",
            "ocndt28c": "Isothermal Layer Depth 28 Celsius",
            # CFS Ocean Temperature
            "ocnsst": "Temperature at depth 5 meters",
            "ocnt15": "Potential temperature 15 meters below",
            "ocnheat": "Heat Content",
            "ocntchp": "Tropical Cyclone Heat Potential",
            # CFS Ocean Salinity
            "ocnsal5": "Salinity at depth 5 meters",
            "ocnsal15": "Salinity at depth 15 meters",
            # CFS Ocean Currents
            "ocnu5": "Zonal Current at depth 5 meters",
            "ocnu15": "Zonal Current at depth 15 meters",
            "ocnv5": "Meridional Current at depth 5 meters",
            "ocnv15": "Meridional Current at depth 15 meters",
            "ocnvv55": "Vertical Velocity at depth 55 meters",
        }

        try:
            self.member
        except NameError:
            print(
                "'member' is not defined. Please set 'member=1` for monthly data for the 6, 12, and 18 UTC cycles, but may be 1, 2, 3, or 4 for the 0 UTC cycle."
            )

        post_root = f"cfs.{self.date:%Y%m%d/%H}/time_grib_{self.member:02d}/{self.product}.{self.member:02d}.{self.date:%Y%m%d%H}.daily.grb2"

        self.SOURCES = {
            "aws": f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}",
            # "azure": f"https://noaacfs.blob.core.windows.net/cfs/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

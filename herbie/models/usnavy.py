## Added by Brian Blaylock
## July 28, 2021


class navgem_godae:
    """
    NAVGEM and NOGAPS on GODAE.

    TODO: Needs work. Study the file naming convention and map to something more sensible.
    https://usgodae.org/docs/layout/mdllayout.pns.html

    - NOGAPS: 2004-2013
    - NAVGEM: 2013-2024

    File examples:
    https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/2023/2023021312/US058GMET-GR1mdl.0018_0056_00000F0RL2023021312_0105_000020-000000air_temp
    https://usgodae.org/ftp/outgoing/fnmoc/models/nogaps/2004/2004010400/US058GMET-GR1mdl.0058_0240_00000F0RL2004010400_0100_000100-000000air_temp
    https://usgodae.org/ftp/outgoing/fnmoc/models/nogaps/2009/2009033012/US058GMET-GR1mdl.0058_0240_00000F0RL2009033012_0105_000100-000000wnd_ucmp
    """

    def template(self):
        self.DESCRIPTION = "Navy Global Environment Model (NAVGEM, 2013-2024) and Navy Operational Global Atmospheric Prediction (NOGAPS, 2004-2013)."
        self.DETAILS = {
            "godae": "https://usgodae.org/",
            "filename_description": "https://usgodae.org/docs/layout/mdllayout.pns.html",
        }

        if self.variable == "HGT:surface":
            # Special case for terrain height
            self.PRODUCTS = {
                "GLND": "Land fields (terrain)",
            }
        else:
            self.PRODUCTS = {
                "GMET": "Meteorological fields",
                "GLND": "Land fields (terrain)",
                "GOCN": "Ocean fields",
                "GCOM": "?",
            }

        # Facilitate familiar shortcuts using wgrib2-style terms to allow
        # - `variable='TMP:2 m'`
        # - `variable='TMP:500 mb'`
        # - `variable='UGRD:10 m'`
        # - `variable='SNOD:surface'`
        # See https://usgodae.org/docs/layout/pn_level_type_tbl.pns.html
        # See https://codes.ecmwf.int/grib/format/grib1/level/3/

        # Map of wgrib2 variable names to GODAE variable names
        variable_map = {
            "TMP": "air_temp",  # Air temperature
            "DEPR": "dwpt_dprs",  # Dew point depression
            "ABSV": "abs_vort",  # Absolute vorticity
            "RH": "rltv_hum",  # Relative Humidity
            "PRES": "pres",  # Pressure
            "UGRD": "wnd_ucmp",  # Wind u-component
            "VGRD": "wnd_vcmp",  # Wind v-component
            "HGT": "geop_ht",  # Geopotential height
            "VAPP": "vpr_pres",  # Vapor pressure
            "VVEL": "wnd_vert_vel",  # Vertical velocity
            "CAPE": "cape",  # CAPE
            "VIS": "visib",  # Visibility
            "PWAT": "prcp_h20",  # Precipitable water (use PWAT:surface)
            "PRATE": "rain_rate",  # Precipitation rate
            "SHTFL": "snsb_heat_flux",  # Sensible heat flux
            "SNOD": "snw_dpth",  # Snow depth
            "NSWRS": "sol_rad",  # Net short-wave radiation flux
            "UFLX": "wnd_strs_ucmp",  # Momentum flux, u-component
            "VFLX": "wnd_strs_vcmp",  # Momentum flux, v-component
            "PRMSL": "pres_msl",  # Mean sea level pressure
        }

        if ":" in self.variable:
            var, lev = self.variable.split(":", maxsplit=1)
            self.variable = variable_map.get(var)
            if var == "HGT" and lev == "surface":
                self.level = "0001_000000-000000"
                self.variable = "terr_ht"
            elif var in {"MSLMA", "PRMSL"}:
                self.level = "0102_000000-000000"
            elif lev.endswith("mb"):
                lev = int(lev.strip("mb").strip())
                self.level = f"0100_{lev:06d}-000000"
            elif lev == "2 m":
                self.level = "0105_000020-000000"
            elif lev == "10 m":
                self.level = "0105_000100-000000"
            elif lev == "surface":
                self.level = "0001_000000-000000"
            elif lev in {"0C", "0C isotherm"}:
                self.level = "0006_000000-000000"
            elif lev in {"tropopause"}:
                self.level = "0007_000000-000000"

        self.SOURCES = {
            "navgem": f"https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/{self.date:%Y/%Y%m%d%H}/US058{self.product}-GR1mdl.0018_0056_{self.fxx:03d}00F0RL{self.date:%Y%m%d%H}_{self.level}{self.variable}",
            "nogaps": f"https://usgodae.org/ftp/outgoing/fnmoc/models/nogaps/{self.date:%Y/%Y%m%d%H}/US058{self.product}-GR1mdl.0058_0240_{self.fxx:03d}00F0RL{self.date:%Y%m%d%H}_{self.level}{self.variable}",
            "navgem grib2": f"https://usgodae.org/ftp/outgoing/fnmoc/models/navgem_0.5/{self.date:%Y/%Y%m%d%H}/US058{self.product}-GR2mdl.0018_0056_{self.fxx:03d}00F0RL{self.date:%Y%m%d%H}_{self.level}{self.variable}.gr2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class navgem_nomads:
    """NAVGEM data from NOMADS (last two days)."""

    def template(self):
        self.DESCRIPTION = "Navy Global Environment Model (NAVGEM) from NOMADS."
        self.DETAILS = {
            "NRL description": "https://www.nrlmry.navy.mil/metoc/nogaps/navgem.html",
            "NOMADS": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/",
        }
        self.PRODUCTS = {
            "none": "",
        }
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/fnmoc/prod/navgem.{self.date:%Y%m%d}/navgem_{self.date:%Y%m%d%H}f{self.fxx:03d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"


class nogaps_ncei:
    """Historical NOGAPS data from NCEI."""

    def template(self):
        self.DESCRIPTION = (
            "Navy Operational Global Atmospheric Prediction System (1997-2008; GRIB1)"
        )
        self.DETAILS = {
            "NCEI description": "https://www.ncei.noaa.gov/products/weather-climate-models/navy-operational-global-atmospheric-prediction?msclkid=ee48a0e7cdb911eca49b9d0ed06548f8",
        }
        self.PRODUCTS = {
            "058_240": "?",
            "058_056": "?",
            "008_240": "?",
            "028_240": "?",
            "041_240": "?",
            "078_240": "?",
            "110_240": "?",
        }
        self.SOURCES = {
            "ncei": f"https://www.ncei.noaa.gov/data/navy-operational-atmostpheric-prediction-system/access/{self.date:%Y%m}/{self.date:%Y%m%d}/nogaps-{self.product}_{self.date:%Y%m%d_%H%M}_000.grb",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
        self.IDX_SUFFIX = [".inv"]

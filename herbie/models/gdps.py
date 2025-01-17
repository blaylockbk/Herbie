## Added by Bryan Guarente (from HRDPS template by Brian Blaylock)
## April 9, 2024

"""
A Herbie template for the GEM Global or Global Deterministic Prediction System (GDPS).

Meteorological Service of Canada (MSC)
The GDPS is Canada's 15 km deterministic global model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/
Data Source: https://dd.weather.gc.ca/model_gem_global/

- Global domain: https://dd.weather.gc.ca/model_gem_global/{res}/grib2/lat_lon/{HH}/{hhh}/

where `HH` is the models initialization time and `hhh` is the forecast lead time.

Data available for last 24 hours.

Other Levels
------------
`variable` is one of {'ACPCP', 'ALBDO', 'APCP', 'CAPE', 'CIN', 'CWAT', 'DLWRF', 'DPT',
'DSWRF', 'GUST_MAX', 'GUST_MIN', 'GUST', 'HPBL', 'KX', 'LHTFL', 'NLWRS', 'NSWRS', 'PRATE',
'PRMSL', 'PTYPE', 'RH', 'SDEN', 'SFCWRO', 'SHTFL', 'SKINT', 'SNOD', 'SOILVIC', 'SOILW',
'SPFH', 'TCDC', 'TMAX', 'TMIN', 'TMP', 'TOTALX', 'TSOIL', 'UGRD', 'ULWRF', 'VGRD', 'WDIR',
'WEAFR', 'WEAPE', 'WEARN', 'WEASN', 'WIND'}
`level` is one of {'SFC', 'EATM', 'TGL_2', 'NTAT', 'TGL_10', 'ISBY_1000-500',
'PVU_1.5', 'PVU_1', 'PVU_2', 'MSL', 'DBLL_100', 'DBLY_10', 'TGL_120', 'TGL_40', 'TGL_80'}

Isobaric Levels
---------------
`variable` is one of {'ABSV', 'DEPR', 'HGT', 'MU-VT-LI', 'RH', 'SHWINX', 'SPFH', 'TMP',
       'UGRD', 'VGRD', 'VVEL', 'WDIR', 'WIND'}
`level` is "ISBL_####" where #### is one of
    {'1', 5', '10', '20', '30', '50', '100', '150',
    '175', '200', '225', '250', '275', '300', '350', '400', '450', '500',
    '550', '600', '650', '700', '750', '800', '850', '875', '900', '925',
    '950', '970', '985', '1000', '1015'}
"""

_variable = {
    "ABSV",
    "ACPCP",
    "ALBDO",
    "APCP",
    "CAPE",
    "CIN",
    "CWAT",
    "DEPR",
    "DLWRF",
    "DPT",
    "DSWRF",
    "GUST_MAX",
    "GUST_MIN",
    "GUST",
    "HGT",
    "HPBL",
    "KX",
    "LHTFL",
    "MU-VT-LI",
    "NLWRS",
    "NSWRS",
    "PRATE",
    "PRES",
    "PRMSL",
    "PTYPE",
    "RH",
    "SDEN",
    "SFCWRO",
    "SHTFL",
    "SHWINX",
    "SKINT",
    "SNOD",
    "SOILVIC",
    "SOILW",
    "SPFH",
    "TCDC",
    "TMAX",
    "TMIN",
    "TMP",
    "TOTALX",
    "TSOIL",
    "UGRD",
    "ULWRF",
    "VGRD",
    "VVEL",
    "WDIR",
    "WEAFR",
    "WEAPE",
    "WEARN",
    "WEASN",
    "WIND",
}

_level = {
    "DBLL_100",
    "DBLY_10",
    "EATM_0",
    "ISBL_1",
    "ISBL_10",
    "ISBL_100",
    "ISBL_1000",
    "ISBL_1015",
    "ISBL_150",
    "ISBL_175",
    "ISBL_20",
    "ISBL_200",
    "ISBL_225",
    "ISBL_250",
    "ISBL_275",
    "ISBL_30",
    "ISBL_300",
    "ISBL_350",
    "ISBL_400",
    "ISBL_450",
    "ISBL_5",
    "ISBL_50",
    "ISBL_500",
    "ISBL_550",
    "ISBL_600",
    "ISBL_650",
    "ISBL_700",
    "ISBL_750",
    "ISBL_800",
    "ISBL_850",
    "ISBL_875",
    "ISBL_900",
    "ISBL_925",
    "ISBL_950",
    "ISBL_970",
    "ISBL_985",
    "ISBY_1000-500",
    "MSL_0",
    "NTAT_0",
    "PVU_1",
    "PVU_1.5",
    "PVU_2",
    "SFC_0",
    "TGL_10",
    "TGL_120",
    "TGL_2",
    "TGL_40",
    "TGL_80",
}


class gdps:
    def template(self):
        if not hasattr(self, "variable"):
            print(
                f"GDPS requires an argument for 'variable'. Here are some ideas:\n{_variable}."
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/"
            )
        if not hasattr(self, "level"):
            print(
                f"GDPS requires an argument for 'level'. Here are some ideas:\n{_level}"
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/"
            )

        self.DESCRIPTION = "Canada's Global Deterministic Prediction System (GDPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "15km/grib2/lat_lon": "global domain",
        }
        PATH = f"{self.date:%H}/{self.fxx:03d}/CMC_glb_{self.variable}_{self.level}_latlon.15x.15_{self.date:%Y%m%d%H}_P{self.fxx:03d}.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/model_gem_global/{self.product}/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

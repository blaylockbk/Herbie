## Added by Bryan Guarente (from HRDPS template by Brian Blaylock)
## April 9, 2024

"""
A Herbie template for the GEM Regional or Regional Deterministic Prediction System (RDPS).

Meteorological Service of Canada (MSC)
The RDPS is Canada's 10 km deterministic regional model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/
Data Source: https://dd.weather.gc.ca/model_gem_regional/

- Regional domain: https://dd.weather.gc.ca/model_gem_regional/{res}/grib2/{HH}/{hhh}/

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
    "HLCY",
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
    "TMP",
    "TOTALX",
    "TSOIL",
    "UGRD",
    "ULWRF",
    "USWRF",
    "VGRD",
    "VVEL",
    "WCHIL",
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
    "IsbL_0001",
    "IsbL_0010",
    "IsbL_0100",
    "IsbL_1000",
    "IsbL_1015",
    "IsbL_0150",
    "IsbL_0175",
    "IsbL_0020",
    "IsbL_0200",
    "IsbL_0225",
    "IsbL_0250",
    "IsbL_0275",
    "IsbL_030",
    "IsbL_0300",
    "IsbL_0350",
    "IsbL_0400",
    "IsbL_0450",
    "IsbL_0005",
    "IsbL_0050",
    "IsbL_0500",
    "IsbL_0550",
    "IsbL_0600",
    "IsbL_0650",
    "IsbL_0700",
    "IsbL_0750",
    "IsbL_0800",
    "IsbL_0850",
    "IsbL_0875",
    "IsbL_0900",
    "IsbL_0925",
    "IsbL_0950",
    "IsbL_0970",
    "IsbL_0985",
    "IsbY_1000-500",
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


class rdps:
    def template(self):
        if not hasattr(self, "variable"):
            print(
                f"RDPS requires an argument for 'variable'. Here are some ideas:\n{_variable}."
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/model_gem_regional/10km/grib2/"
            )
        if not hasattr(self, "level"):
            print(
                f"RDPS requires an argument for 'level'. Here are some ideas:\n{_level}"
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/model_gem_regional/10km/grib2/"
            )

        self.DESCRIPTION = "Canada's Regional Deterministic Prediction System (RDPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "hrdps": "regional domain",
        }

        PATH = f"{self.date:%H}/{self.fxx:03d}/{self.date:%Y%m%dT%HZ}_MSC_RDPS_{self.variable}_{self.level}_RLatLon0.09_PT{self.fxx:03d}H.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_rdps/10km/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


# https://dd.weather.gc.ca/2025101500/WXO-DD/model_rdps/10km/00/000/20251015T00Z_MSC_RDPS_AirTemp_ISBL_0550_RLatLon0.09_PT000H.grib2

# https://dd.weather.gc.ca/20251005/WXO-DD/model_rdps/10km/00/000/20251005T00Z_MSC_RDPS_AirTemp_IsbL_0550_RLatLon0.09_PT000H.grib2
# https://dd.weather.gc.ca/20251005/WXO-DD/model_rdps/10km/00/000/20251005T00Z_MSC_RDPS_AirTemp_IsbL-0550_RLatLon0.09_PT000H.grib2

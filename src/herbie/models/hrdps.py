## Added by Brian Blaylock
## June 21, 2023
## Updated by Bryan Guarente
## April 9, 2024

"""
A Herbie template for the High Resolution Deterministic Prediction System (HRDPS).

Meteorological Service of Canada (MSC)
The HRDPS is Canada's 2.5 km deterministic model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/#data-location
Data Source: https://dd.weather.gc.ca/model_hrdps/

- Continental domain: https://dd.weather.gc.ca/model_hrdps/continental/{res}/{HH}/{hhh}/
- North domain (experimental): https://dd.weather.gc.ca/model_hrdps/north/grib2/{HH}/{hhh}/

where `HH` is the models initialization time and `hhh` is the forecast lead time.

Data available for last 24 hours.

Other Levels
------------
`variable` is one of {'ALBDO', 'CAPE', 'CWAT', 'DEN', 'DEPR', 'DLWRF', 'DPT', 'DSWRF',
       'GUST-Max', 'GUST-Min', 'GUST', 'HGT', 'HLCY', 'HPBL', 'ICEC',
       'LAND', 'LHTFL', 'NLWRS', 'NSWRS', 'PRES', 'PRMSL', 'RH', 'SDEN',
       'SDWE', 'SFCWRO', 'SHTFL', 'SKINT', 'SNOD', 'SOILVIC', 'SOILW',
       'SPFH', 'TCDC', 'TMP', 'TSOIL', 'UGRD', 'ULWRF', 'USWRF', 'UTCI',
       'VGRD', 'WDIR', 'WIND', 'WTMP'}
`level` is one of {'Sfc', 'EATM', 'AGL-120m', 'AGL-40m', 'AGL-80m', 'AGL-2m', 'NTAT',
       'AGL-10m', 'ISBY-1000-500', 'MSL', 'DBS-0-10cm', 'DBS-0-1cm'}

Isobaric Levels
---------------
`variable` is one of {'ABSV', 'DEPR', 'HGT', 'MU-VT-LI', 'RH', 'SHWINX', 'SPFH', 'TMP',
       'UGRD', 'VGRD', 'VVEL', 'WDIR', 'WIND'}
`level` is "ISBL_####" where #### is one of
    {'0250', '0500', '0700', '0850', '1000', '0050', '0100', '0150',
    '0175', '0200', '0225', '0275', '0300', '0350', '0400', '0450',
    '0550', '0600', '0650', '0750', '0800', '0875', '0900', '0925',
'0950', '0970', '0985', '1015'}
"""

_variable = {
    "ABSV",
    "ACPCP",
    "ALBDO",
    "APCP",
    "CAPE",
    "CWAT",
    "DEN",
    "GUST_MAX",
    "GUST_MIN",
    "DEPR",
    "DLWRF",
    "DPT",
    "DSWRF",
    "GUST-Max",
    "GUST-Min",
    "GUST",
    "HGT",
    "HLCY",
    "HPBL",
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
    "SDWE",
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
    "TSOIL",
    "UGRD",
    "ULWRF",
    "USWRF",
    "UTCI",
    "VGRD",
    "VI",
    "VVEL",
    "WDIR",
    "WEAFR",
    "WEAPE",
    "WEARN",
    "WEASN",
    "WIND",
}

_level = {
    "AGL-10m",
    "AGL-120m",
    "AGL-2m",
    "AGL-40m",
    "AGL-80m",
    "DBS-0-10cm",
    "DBS-0-1cm",
    "EATM",
    "ISBL_100",
    "ISBL_1000",
    "ISBL_1015",
    "ISBL_0150",
    "ISBL_0175",
    "ISBL_0200",
    "ISBL_0225",
    "ISBL_0250",
    "ISBL_0275",
    "ISBL_0300",
    "ISBL_0350",
    "ISBL_0400",
    "ISBL_0450",
    "ISBL_0050",
    "ISBL_0500",
    "ISBL_0550",
    "ISBL_0600",
    "ISBL_0650",
    "ISBL_0700",
    "ISBL_0750",
    "ISBL_0800",
    "ISBL_0850",
    "ISBL_0875",
    "ISBL_0900",
    "ISBL_0925",
    "ISBL_0950",
    "ISBL_0970",
    "ISBL_0985",
    "ISBY-1000-500",
    "MSL",
    "NTAT",
    "Sfc",
    "TGL_10",
}


class hrdps:
    def template(self):
        if not hasattr(self, "variable"):
            print(
                f"HRDPS requires an argument for 'variable'. Here are some ideas:\n{_variable}."
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/<YYYYMMDD>/WXO-DD/model_hrdps/"
            )
        if not hasattr(self, "level"):
            print(
                f"HRDPS requires an argument for 'level'. Here are some ideas:\n{_level}"
            )
            print(
                "For full list of files, see https://dd.weather.gc.ca/<YYYYMMDD>/WXO-DD/model_hrdps/"
            )

        self.DESCRIPTION = (
            "Canada's High Resolution Deterministic Prediction System (HRDPS)"
        )
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "continental": "Continental domain (2.5 km)",
            "north": "North domain (3 km)",
        }

        if self.product == "continental":
            resolution = "2.5km"
            resolution2 = "RLatLon0.0225"
            alt_path1 = "HRDPS"
            alt_path2 = "HRDPS-WEonG"
        elif self.product == "north":
            resolution = "3km"
            resolution2 = "RLatLon0.03"
            alt_path1 = "HRDPS-North"
            alt_path2 = "HRDPS-North-WEonG"
        else:
            resolution = "2.5km"
            resolution2 = "RLatLon0.0225"
            alt_path1 = "HRDPS"
            alt_path2 = "HRDPS-WEonG"

        PATH = f"{self.date:%H}/{self.fxx:03d}/{self.date:%Y%m%dT%HZ}_MSC_{alt_path1}_{self.variable}_{self.level}_{resolution2}_PT{self.fxx:03d}H.grib2"

        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_hrdps/{self.product}/{resolution}/{PATH}",
            "msc-WEonG": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_hrdps/{self.product}/{resolution}/{PATH.replace(f'_{alt_path1}_', f'_{alt_path2}_')}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

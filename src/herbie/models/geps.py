## Added by Karl Schneider
## April 2026

"""
A Herbie template for GEPS (Global Ensemble Prediction System).

Meteorological Service of Canada (MSC)
The GEPS is Canada's ensemble global model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_geps/readme_geps-datamart_en/
Data Source: https://dd.weather.gc.ca/ensemble/geps/

- Ensemble domain: https://dd.weather.gc.ca/{YYYYMMDD}/WXO-DD/ensemble/geps/grib2/{product}/{HH}/{hhh}/

where `YYYYMMDDHH` is the model init date, `HH` is the model init time (ensemble cycle),
and `hhh` is the forecast lead time. Products are 'geps-prod' or 'geps-raw'.

GEPS Products
-----------
geps-prod: Processed ensemble products (directory `grib2/products`)
geps-raw: Raw ensemble member output (directory `grib2/raw`)
"""

_geps_prod_products = {
    "CAPE",
    "CIN",
    "DEPR",
    "DLWRF",
    "DPT",
    "DSWRF",
    "GUST",
    "HEATX",
    "HGT",
    "HPBL",
    "KX",
    "LHTFL",
    "MU-VT-LI",
    "PRATE",
    "PRMSL",
    "PTYPE",
    "RH",
    "SHWINX",
    "SKINT",
    "SNOD",
    "SPFH",
    "TCDC",
    "TMAX",
    "TMIN",
    "TMP",
    "UGRD",
    "ULWRF",
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

_geps_raw_products = {
    "ABSV",
    "ACPCP",
    "ALERT",
    "APCP",
    "CAPE",
    "CIN",
    "CWAT",
    "DEPR",
    "DLWRF",
    "DPT",
    "DSWRF",
    "GUST",
    "HGT",
    "HPBL",
    "KX",
    "LHTFL",
    "NLWRS",
    "NSWRS",
    "PRATE",
    "PRES",
    "PRMSL",
    "PTYPE",
    "RH",
    "SNOD",
    "SPFH",
    "TCDC",
    "TMP",
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


def _normalize_geps_level(level: str) -> str:
    """Normalize GEPS level token to match Datamart filename conventions.

    GEPS filenames use zero-padded isobaric levels (e.g., ISBL_0850, ISBL_0050).
    Accept user input like ISBL_850 or ISBL_50 and normalize it for URL generation.
    """
    if not isinstance(level, str):
        return level

    if level.startswith("ISBL_"):
        pressure = level.split("_", 1)[1]
        if pressure.isdigit():
            return f"ISBL_{int(pressure):04d}"

    return level


class geps:
    def template(self):
        # Set default product if not specified
        if self.product is None:
            self.product = "geps-prod"

        # Backward-compatible aliases to normalized product names.
        product_aliases = {
            "geps-prod": "geps-prod",
            "products": "geps-prod",
            "prod": "geps-prod",
            "geps-raw": "geps-raw",
            "raw": "geps-raw",
            "members": "geps-raw",
        }

        self.product = product_aliases.get(self.product, self.product)

        # Validate product
        if self.product not in ["geps-prod", "geps-raw"]:
            raise ValueError(
                f"product={self.product} not recognized. Must be one of ['geps-prod', 'geps-raw']"
            )

        # Get appropriate product list based on product type
        if self.product == "geps-prod":
            valid_products = _geps_prod_products
            product_directory = "products"
            filename_prefix = "CMC_geps-prob"
            filename_tail = "all-products"
        else:
            valid_products = _geps_raw_products
            product_directory = "raw"
            filename_prefix = "CMC_geps-raw"
            filename_tail = "allmbrs"

        if not hasattr(self, "variable"):
            print(
                f"GEPS requires an argument for 'variable'. "
                f"For {self.product}, here are some ideas:\n{sorted(valid_products)}"
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/geps/grib2/{product_directory}/"
            )

        if not hasattr(self, "level"):
            print(f"GEPS requires an argument for 'level'. Here are some ideas:\n{_level}")
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/geps/grib2/{product_directory}/"
            )

        self.DESCRIPTION = "Canada's Global Ensemble Prediction System (GEPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_geps/readme_geps-datamart_en/",
        }
        self.PRODUCTS = {
            "geps-prod": "processed ensemble products (probabilities, means, etc.); files served from grib2/products",
            "geps-raw": "raw ensemble member output; files served from grib2/raw",
        }
        self.AVAILABLE_VARIABLES = sorted(_geps_prod_products | _geps_raw_products)
        self.AVAILABLE_LEVELS = sorted(_level)

        level_for_filename = _normalize_geps_level(self.level)

        PATH = f"{self.date:%H}/{self.fxx:03d}/{filename_prefix}_{self.variable}_{level_for_filename}_latlon0p5x0p5_{self.date:%Y%m%d%H}_P{self.fxx:03d}_{filename_tail}.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/geps/grib2/{product_directory}/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

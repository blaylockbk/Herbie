## Added by GitHub Copilot
## April 2026

"""
A Herbie template for REPS (Regional Ensemble Prediction System).

Meteorological Service of Canada (MSC)
The REPS is Canada's regional ensemble model at 10 km.

Data Source: https://dd.weather.gc.ca/ensemble/reps/

- Ensemble domain:
  https://dd.weather.gc.ca/{YYYYMMDD}/WXO-DD/ensemble/reps/10km/grib2/{HH}/{hhh}/

where `YYYYMMDDHH` is the model init date, `HH` is the model init time,
and `hhh` is the forecast lead time.
"""

_variable = {
    "AFRAIN",
    "AICEP",
    "APCP",
    "ARAIN",
    "ASNOW",
    "DLWRF",
    "DSWRF",
    "FPRATE-Accum6h-Prob",
    "HEATX-Prob",
    "HGT",
    "IPRATE-Accum6h-Prob",
    "LHTFL",
    "PRES",
    "PRMSL",
    "RH",
    "RPRATE-Accum6h-Prob",
    "SFCWRO",
    "SHTFL",
    "SNOD",
    "SPFH",
    "SPRATE-Accum6h-Prob",
    "TCDC",
    "TMP",
    "TMP-Prob",
    "TPRATE-Accum3h-Prob",
    "TPRATE-Accum6h-Prob",
    "TSOIL",
    "UGRD",
    "ULWRF",
    "VGRD",
    "VSOILM",
    "WCF-Prob",
    "WEASD",
    "WIND",
    "WIND-Prob",
}

_level = {
    "AGL-10m",
    "AGL-120m",
    "AGL-2m",
    "AGL-40m",
    "AGL-80m",
    "DBS-10cm",
    "ISBL-0050",
    "ISBL-0100",
    "ISBL-0200",
    "ISBL-0250",
    "ISBL-0500",
    "ISBL-0700",
    "ISBL-0850",
    "ISBL-0925",
    "ISBL-1000",
    "MSL",
    "NTAT",
    "SFC",
}


class reps:
    def template(self):
        if self.product is None:
            self.product = "10km/grib2"

        if self.product != "10km/grib2":
            raise ValueError(
                f"product={self.product} not recognized. Must be '10km/grib2'."
            )

        if not hasattr(self, "variable"):
            print(
                f"REPS requires an argument for 'variable'. Here are some ideas:\n{sorted(_variable)}."
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/reps/10km/grib2/"
            )

        if not hasattr(self, "level"):
            print(f"REPS requires an argument for 'level'. Here are some ideas:\n{sorted(_level)}")
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/reps/10km/grib2/"
            )

        self.DESCRIPTION = "Canada's Regional Ensemble Prediction System (REPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_reps/readme_reps-datamart_en/",
        }
        self.PRODUCTS = {
            "10km/grib2": "regional 10 km ensemble domain",
        }
        self.AVAILABLE_VARIABLES = sorted(_variable)
        self.AVAILABLE_LEVELS = sorted(_level)

        PATH = (
            f"{self.date:%H}/{self.fxx:03d}/"
            f"{self.date:%Y%m%dT%HZ}_MSC_REPS_{self.variable}_{self.level}_"
            f"RLatLon0.09x0.09_PT{self.fxx:03d}H.grib2"
        )
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/ensemble/reps/{self.product}/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

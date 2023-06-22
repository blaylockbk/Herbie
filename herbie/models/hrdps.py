## Added by Brian Blaylock
## June 21, 2023

"""
A Herbie template for the High Resolution Deterministic Prediction System (HRDPS)

Meteorological Service of Canada (MSC)
The HRDPS is Canada's 2.5 km deterministic model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/#data-location
Data Source: https://dd.weather.gc.ca/model_hrdps/
"""


class hrdps:
    def template(self):
        self.DESCRIPTION = (
            "Canada's High Resolution Deterministic Prediction System (HRDPS)"
        )
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "continental": "",
        }
        PATH = f"2.5km/{self.date:%H}/{self.fxx:03d}/{self.date:%Y%m%dT%HZ}_MSC_HRDPS-WEonG_{self.variable}_{self.level}_RLatLon0.0225_PT{self.fxx:03d}H.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/model_hrdps/{self.product}/{PATH}",
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

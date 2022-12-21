## Added by Brian Blaylock
## May 6, 2022


class nogaps:
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

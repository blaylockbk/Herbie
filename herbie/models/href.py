## Added by Karl Schneider (June 2024)

"""
A Herbie template for the The High Resolution Ensemble Forecast (HREF).

Description
-----------
The High Resolution Ensemble Forecast (HREF) produces ensemble products from several different models running at ~3 km horizontal grid spacing. Three of the models utilized in HREF come from the High Resolution Window (HiresW): two different configurations of the Advanced Research Weather Research and Forecasting (WRF-ARW) model and a Finite Volume Cubed Sphere (FV3) run. The North American Model (NAM) 3 km CONUS nest is utilized only for the CONUS HREF, and the High Resolution Rapid Refresh (HRRR) is used for the CONUS and AK domains. Information from these models is used in a time-lagged fashion, with the two most recent runs of each system combined into an 10-member ensemble for CONUS, an 8-member ensemble for AK, and a 6-member ensemble for HI and PR. This system produces ensemble products for four different domains on the following schedule, with output at hourly temporal resolution to 48 h:

00Z (CONUS and Hawaii)
06Z (CONUS, Alaska, and Puerto Rico)
12Z (CONUS and Hawaii)
18Z (CONUS, Alaska, and Puerto Rico)

URL structure: https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/href.{YYYYMMDD}/ensprod/href.t{HH}z.{domain}.{product}.f{hh}.grib2

where `HH` is the model initialization time and `hh` is the forecast lead time.

Available Products
------------------
mean: Arithmetic mean of all members.
pmmn: A “probability matched” mean, which combines information from the ensemble mean with the amplitude of the individual members. This version is computed over the full domain simultaneously.
lpmm : A localized “probability matched” mean, which combines information from the ensemble mean with the amplitude of the individual members. This version is computed over small regions, which then are assembled to cover the full domain. Only for precipitation.
avrg: An averaging of the mean and pmmn output. Only for precipitation.
sprd: The spread of the ensemble, which is a measure of how different the individual model runs are for a variable at a given point (smaller spread indicates better agreement within the ensemble)
prob: Probabilistic output; the percentage of the membership meeting a specified threshold such as > 0.5” of accumulated precipitation in a 6 h period). A mix of point probabilities and neighborhood maximum probabilities.
eas: Ensemble Agreement Scale (EAS) probability, which is a smoothed fractional probability, where the size of the neighborhood for computing the fractional probability varies over a 10-100 km radius (smaller radius used where model members agree closely; larger radius used where there is less agreement). Only for precipitation and snow probability products.

Available Domains
-----------------
"conus": lower-48 US domain
"ak": Alaska domain
"hi": Hawaii domain
"pr": Puerto Rico domain

"""

_domain = {
    "conus",
    "ak",
    "hi",
    "pr",
}


class href:
    def template(self):
        if not hasattr(self, "domain"):
            print(
                f"HREF requires an argument for 'domain'. Here are some ideas:\n{_domain}"
            )
        self.DESCRIPTION = "The High Resolution Ensemble Forecast (HREF)"
        self.DETAILS = {
            "Product description": "https://nomads.ncep.noaa.gov/",
        }
        self.PRODUCTS = {
            "mean": "Arithmetic mean of all members.",
            "pmmn": "A “probability matched” mean, which combines information from the ensemble mean with the amplitude of the individual members. This version is computed over the full domain simultaneously.",
            "lpmm": "A localized “probability matched” mean, which combines information from the ensemble mean with the amplitude of the individual members. This version is computed over small regions, which then are assembled to cover the full domain. Only for precipitation.",
            "avrg": "An averaging of the mean and pmmn output. Only for precipitation.",
            "sprd": "The spread of the ensemble, which is a measure of how different the individual model runs are for a variable at a given point (smaller spread indicates better agreement within the ensemble)",
            "prob": "Probabilistic output; the percentage of the membership meeting a specified threshold such as > 0.5” of accumulated precipitation in a 6 h period). A mix of point probabilities and neighborhood maximum probabilities.",
            "eas": "Ensemble Agreement Scale (EAS) probability, which is a smoothed fractional probability, where the size of the neighborhood for computing the fractional probability varies over a 10-100 km radius (smaller radius used where model members agree closely; larger radius used where there is less agreement). Only for precipitation and snow probability products.",
        }
        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/href.{self.date:%Y%m%d}/ensprod/href.t{self.date:%H}z.{self.domain}.{self.product}.f{self.fxx:02d}.grib2"
        }
        self.IDX_SUFFIX = [".grib2.idx", ".idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

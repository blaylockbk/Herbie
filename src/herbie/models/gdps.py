## Added by Bryan Guarente (from HRDPS template by Brian Blaylock)
## April 9, 2024

"""
A Herbie template for the GEM Global or Global Deterministic Prediction System (GDPS).

Meteorological Service of Canada (MSC)
The GDPS is Canada's 15 km deterministic global model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/
Data Source: https://dd.weather.gc.ca/model_gdps/

- Global domain: https://dd.weather.gc.ca/{YYYYMMDD}/WXO-DD/model_gdps/{res}/{HH}/{hhh}/

where `YYYYMMDDHH` is the model init date, `HH` is the model init time and `hhh` is the forecast lead time.


Levels (match Datamart filenames exactly)
-----------------------------------------
Other levels: 'Sfc', 'MSL', 'EAtm', 'NTAtm', 'DBS-0to10cm', 'DBS-0to1cm', 'PVU-1', 'PVU-1.5', 'PVU-2',
'AGL-2m', 'AGL-40m', 'AGL-80m', 'AGL-120m','EtaL-10000', 'EtaL-6500', 'IsbL-0850to0700',
'IsbL-1000to0500', 'IsbL-1000to0850'

Isobaric Levels (format: IsbL-XXXX)
---------------
Pressure levels (hPa): 0001, 0005, 0010, 0020, 0030, 0050, 0100, 0150, 0175, 0200, 0225, 0250, 0275,
0300, 0350, 0400, 0450, 0500, 0550, 0600, 0650, 0700, 0750, 0800, 0850, 0875, 0900, 0925, 0950, 0970, 0985, 1000, 1015
"""

_variable = {
    "AbsoluteVorticity",
    "AirTemp",
    "Albedo",
    "CAPE",
    "CIN",
    "CloudWater",
    "ConvectivePrecip-Accum",
    "DewPointDepression",
    "DownwardLongwaveRadiationFlux-Accum",
    "DownwardShortwaveRadiationFlux-Accum",
    "FreezingRain-Accum24h",
    "FreezingRain-Accum12h",
    "FreezingRain-Accum6h",
    "FreezingRain-Accum3h",
    "FreezingRain-Accum1h",
    "FreezingRain-Accum",
    "GeopotentialHeight",
    "HighLowPressure",
    "Humidex",
    "IcePellets-Accum24h",
    "IcePellets-Accum12h",
    "IcePellets-Accum6h",
    "IcePellets-Accum3h",
    "IcePellets-Accum1h",
    "IcePellets-Accum",
    "LatentHeatNetFlux",
    "LiftedIndex-MU-VT",
    "NetLongwaveRadiationFlux-Accum",
    "NetShortwaveRadiationFlux-Accum",
    "O3MixingRatio",
    "O3",
    "PlanetaryBoundaryLayerHeight",
    "Precip-Accum24h",
    "Precip-Accum12h",
    "Precip-Accum6h",
    "Precip-Accum3h",
    "Precip-Accum1h",
    "Precip-Accum",
    "PrecipRate_Sfc",
    "PrecipType-Instant",
    "Pressure",
    "RadiativeTemp",
    "Rain-Accum24h",
    "Rain-Accum12h",
    "Rain-Accum6h",
    "Rain-Accum3h",
    "Rain-Accum1h",
    "RelativeHumidity",
    "Runoff-Accum",
    "SensibleHeatNetFlux",
    "ShowalterIndex",
    "Snow-Accum24h",
    "Snow-Accum12h",
    "Snow-Accum6h",
    "Snow-Accum3h",
    "Snow-Accum1h",
    "SnowDensity",
    "SnowDepth",
    "SoilVolumetricIceContent",
    "SpecificHumidity",
    "Thickness",
    "TotalCloudCover",
    "TotalTotalsIndex",
    "UVIndex-ClearSky",
    "UVIndex",
    "UpwardLongwaveRadiationFlux",
    "VerticalVelocity",
    "WindChill",
    "WindDir",
    "WindGust-Max",
    "WindGust-Min",
    "WindGust",
    "WindSpeed",
    "WindU",
    "WindV",
}

_level = {
    "DBS-0to1cm",
    "DBS-0to10cm",
    "EAtm",
    "IsbL-0850to0700",
    "IsbL-1000to0500",
    "IsbL-1000to0850",
    "IsbL-0001",
    "IsbL-0010",
    "IsbL-0100",
    "IsbL-1000",
    "IsbL-1015",
    "IsbL-0150",
    "IsbL-0175",
    "IsbL-0020",
    "IsbL-0200",
    "IsbL-0225",
    "IsbL-0250",
    "IsbL-0275",
    "IsbL-0030",
    "IsbL-0300",
    "IsbL-0350",
    "IsbL-0400",
    "IsbL-0450",
    "IsbL-0005",
    "IsbL-0050",
    "IsbL-0500",
    "IsbL-0550",
    "IsbL-0600",
    "IsbL-0650",
    "IsbL-0700",
    "IsbL-0750",
    "IsbL-0800",
    "IsbL-0850",
    "IsbL-0875",
    "IsbL-0900",
    "IsbL-0925",
    "IsbL-0950",
    "IsbL-0970",
    "IsbL-0985",
    "MSL",
    "NTAtm",
    "PVU-1",
    "PVU-1.5",
    "PVU-2",
    "Sfc",
    "AGL-10m",
    "AGL-120m",
    "AGL-2m",
    "AGL-40m",
    "AGL-80m",
}


class gdps:
    def template(self):
        if self.product is None:
            self.product = "15km"

        product_aliases = {
            "15km/grib2/lat_lon": "15km",
        }
        self.product = product_aliases.get(self.product, self.product)

        if not hasattr(self, "variable"):
            print(
                f"GDPS requires an argument for 'variable'. Here are some ideas:\n{_variable}."
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_gdps/15km/"
            )
        if not hasattr(self, "level"):
            print(
                f"GDPS requires an argument for 'level'. Here are some ideas:\n{_level}"
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_gdps/15km/"
            )

        self.DESCRIPTION = "Canada's Global Deterministic Prediction System (GDPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "15km": "global domain",
        }
        PATH = f"{self.date:%H}/{self.fxx:03d}/{self.date:%Y%m%dT%HZ}_MSC_GDPS_{self.variable}_{self.level}_LatLon0.15_PT{self.fxx:03d}H.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_gdps/{self.product}/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

## Added by Bryan Guarente (from HRDPS template by Brian Blaylock)
## April 9, 2024

"""
A Herbie template for the GEM Regional or Regional Deterministic Prediction System (RDPS).

Meteorological Service of Canada (MSC)
The RDPS is Canada's 10 km deterministic regional model

Description: https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/
Data Source: https://dd.weather.gc.ca/model_rdps/

- Regional domain: https://dd.weather.gc.ca/{YYYYMMDD}/WXO-DD/model_rdps/10km/{HH}/{hhh}/

where `HH` is the models initialization time and `hhh` is the forecast lead time.

Data available for last 24 hours.

Levels (match Datamart filenames exactly)
-----------------------------------------
Other levels: 'Sfc', 'MSL', 'EAtm', 'NTAtm', 'DBS-0to10cm', 'DBS-0to1cm', 'PVU-1', 'PVU-1.5', 'PVU-2',
'AGL-2m', 'AGL-40m', 'AGL-80m', 'AGL-120m', 'TGL-2', 'TGL-10', 'TGL-40', 'TGL-80', 'TGL-120',
'EtaL-10000', 'EtaL-6500', 'IsbL-0850to0700', 'IsbL-1000to0500', 'IsbL-1000to0850'

Isobaric Levels (format: IsbL-XXXX)
-----------------------------------
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
    "DewPointDepression",
    "DewPoint",
    "DownwardLongwaveRadiationFlux-Accum",
    "DownwardShortwaveRadiationFlux-Accum",
    "GeopotentialHeight",
    "Humidex",
    "KIndex",
    "LandWaterProportion",
    "LatentHeatNetFlux",
    "LiftedIndex-MU-VT",
    "NetLongwaveRadiationFlux-Accum",
    "NetShortwaveRadiationFlux-Accum",
    "PlanetaryBoundaryLayerHeight",
    "PrecipType-Instant",
    "Pressure",
    "RadiativeTemp",
    "RelativeHumidity",
    "Runoff-Accum",
    "SWEATIndex",
    "SeaIceFraction",
    "SeaWaterTemp",
    "SensibleHeatNetFlux",
    "ShowalterIndex",
    "SkyTransparencyIndex",
    "SnowDensity",
    "SnowDepth",
    "SoilTemp",
    "SoilVolumetricWaterContent",
    "SpecificHumidity",
    "StormRelativeHelicity",
    "StormSeverityIndex",
    "Thickness",
    "TotalCloudCover",
    "TotalTotalsIndex",
    "UVIndex-ClearSky-Max24h",
    "UVIndex-ClearSky",
    "UVIndex-Max24h",
    "UVIndex",
    "UpwardLongwaveRadiationFlux",
    "UpwardShortwaveRadiationFlux",
    "VerticalVelocity",
    "VerticalWindShear",
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
    # Other levels
    "Sfc",
    "MSL",
    "EAtm",
    "NTAtm",
    "DBS-0to10cm",
    "DBS-0to1cm",
    "PVU-1",
    "PVU-1.5",
    "PVU-2",
    "AGL-2m",
    "AGL-10m",
    "AGL-40m",
    "AGL-80m",
    "AGL-120m",
    "TGL-2",
    "TGL-10",
    "TGL-40",
    "TGL-80",
    "TGL-120",
    "EtaL-10000",
    "EtaL-6500",
    "IsbL-0850to0700",
    "IsbL-1000to0500",
    "IsbL-1000to0850",
    # Isobaric levels (IsbL-XXXX format)
    "IsbL-0001",
    "IsbL-0005",
    "IsbL-0010",
    "IsbL-0020",
    "IsbL-0030",
    "IsbL-0050",
    "IsbL-0100",
    "IsbL-0150",
    "IsbL-0175",
    "IsbL-0200",
    "IsbL-0225",
    "IsbL-0250",
    "IsbL-0275",
    "IsbL-0300",
    "IsbL-0350",
    "IsbL-0400",
    "IsbL-0450",
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
    "IsbL-1000",
    "IsbL-1015",
}


class rdps:
    def template(self):
        if self.product is None:
            self.product = "10km/grib2"

        product_aliases = {
            "10km/grib2": "10km/grib2",
            "10km": "10km/grib2",
            "hrdps": "10km/grib2",
        }
        self.product = product_aliases.get(self.product, self.product)

        if self.product != "10km/grib2":
            raise ValueError(
                f"product={self.product} not recognized. Must be '10km/grib2'."
            )

        if not hasattr(self, "variable"):
            print(
                f"RDPS requires an argument for 'variable'. Here are some ideas:\n{_variable}."
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_rdps/10km/"
            )
        if not hasattr(self, "level"):
            print(
                f"RDPS requires an argument for 'level'. Here are some ideas:\n{_level}"
            )
            print(
                f"For full list of files, see https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_rdps/10km/"
            )

        self.DESCRIPTION = "Canada's Regional Deterministic Prediction System (RDPS)"
        self.DETAILS = {
            "Datamart product description": "https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/#data-location",
        }
        self.PRODUCTS = {
            "10km/grib2": "regional 10 km domain",
        }
        self.AVAILABLE_VARIABLES = sorted(_variable)
        self.AVAILABLE_LEVELS = sorted(_level)

        PATH = f"{self.date:%H}/{self.fxx:03d}/{self.date:%Y%m%dT%HZ}_MSC_RDPS_{self.variable}_{self.level}_RLatLon0.09_PT{self.fxx:03d}H.grib2"
        self.SOURCES = {
            "msc": f"https://dd.weather.gc.ca/{self.date:%Y%m%d}/WXO-DD/model_rdps/10km/{PATH}"
        }

        self.IDX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

"""
A Herbie template for the ECMWF Open Data GRIB2 files.

See the `media release <https://www.ecmwf.int/en/about/media-centre/news/2022/ecmwf-makes-wide-range-data-openly-available>`_.

- Copyright statement: Copyright "© 2022 European Centre for Medium-Range Weather Forecasts (ECMWF)".
- Source www.ecmwf.int
- License Statement: This data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0). https://creativecommons.org/licenses/by/4.0/
- Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their use.

https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS

Update 2024-02-29: ECMWF changes from 0.4 degree resolution to 0.25 plus adds artificial IFS
https://www.ecmwf.int/en/about/media-centre/news/2024/ecmwf-releases-much-larger-open-dataset

"""

from datetime import datetime

POSSIBLE_VALUES = {
    "type": ["tf", "fc", "fcmean", "cf", "pf", "em", "ep", "es"],
    "stream": ["oper", "wave", "scda", "scwv", "enfo", "waef", "mmsa"],
    "resol": ["0p25", "0p1", "0p4-beta"],
}
LEVTYPE_FILES = {"sfc": "-sfc", "sol": "-sfc", "pl": "-pl"}
SFC_ONLY_STREAMS = {"wave", "waef", "scwv"}

# Resolutions whose GRIB files are split by level type into
# "<name>-sfc.grib2" and "<name>-pl.grib2" instead of a single file
SPLIT_RESOLUTIONS = {"0p1"}
# Resolutions only produced by the IFS model
IFS_ONLY_RESOLUTIONS = {"0p1"}

def level_files(product, resolution, type, for_index):
    # Files at a split resolution are separated into single level ("-sfc")
    # and pressure level ("-pl") files. If no levtype is requested, both are
    # returned so that the result matches what the single file would contain.
    if resolution not in SPLIT_RESOLUTIONS or type == "tf":
        return [""]

    if product in SFC_ONLY_STREAMS:
            return [LEVTYPE_FILES["sfc"]]

    levtypes = [x for x in for_index.get("levtype", []) if x in LEVTYPE_FILES]
    if not levtypes:
        #levtypes = ["sfc", "pl"]
        levtypes = ["sfc"]

    return list(dict.fromkeys(LEVTYPE_FILES[x] for x in levtypes))


class ifs:

    def template(self):

        IFS_50R1_DATE = datetime(2026, 5, 12, tzinfo=self.date.tzinfo)
        
        # Allow a user to select the deprecated 0p4-beta resolution,
        # but default to the 0p25 product if resolution is not specified.
        # Sounds like the 0p4-beta product will be deprecated in May 2024.
        # Resolutoin 0p1 is available since 20-10-2026
        if not hasattr(self, "resolution") or self.resolution is None:
            self.resolution = "0p25"
            if self.date < datetime(2024, 2, 1, tzinfo=self.date.tzinfo):
                self.resolution = "0p4-beta"
                
        if self.resolution not in POSSIBLE_VALUES["resol"]:
            raise ValueError(f"Bad resolution {self.resolution}")
        
        self.DESCRIPTION = "ECMWF Open Data - Integrated Forecast System"
        self.DETAILS = {
            "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        }
        # this is ECMWF stream
        self.PRODUCTS = {
            "oper": "operational high-resolution forecast, atmospheric fields",
            "enfo": "ensemble forecast, atmospheric fields",
            "wave": "wave forecasts",
            "waef": "ensemble forecast, ocean wave fields,",
            "scda": "short cut-off high-resolution forecast, atmospheric fields (also known as high-frequency products)",
            "scwv": "short cut-off high-resolution forecast, ocean wave fields (also known as high-frequency products)",
            "mmsf": "multi-model seasonal forecasts fields from the ECMWF model only.",
        }

        # example file
        # https://data.ecmwf.int/forecasts/20240229/00z/ifs/0p25/oper/20240229000000-0h-oper-fc.grib2

        # IFS_50R1_DATE
        if self.date >= IFS_50R1_DATE:
            if self.product == "scda":
                self.product = "oper"
            if self.product == "scwv":
                self.product = "wave"

        if self.product not in POSSIBLE_VALUES["stream"]:
            raise ValueError(f"Bad product {self.product}")

        # file pattern "{_yyyymmddHHMMSS}-{step}h-{_stream}-{type}{_levfile}.{_extension}"
        # product_suffix = {type}{_levfile}
        self.type = "" # could by fc ef or tf
        _levfile = level_files(self.product, self.resolution, self.type, {"levtype":"sfc"})[0]
        print(_levfile)

        # product suffix
        if self.product in ["enfo", "waef"]:
            product_suffix = "ef" + _levfile
        else:
            product_suffix = "fc" + _levfile

        if self.date < datetime(2024, 2, 28, 6, tzinfo=self.date.tzinfo):
            post_root = (
                f"{self.date:%Y%m%d/%Hz}/{self.resolution}/{self.product}"
                f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
            )
        else:
            post_root = (
                f"{self.date:%Y%m%d/%Hz}/ifs/{self.resolution}/{self.product}"
                f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
            )

        print(post_root)

        # If user asks for 'oper' or 'wave', still look for data in scda and waef for the short cut-off high resolution forecast.
        self.SOURCES = {
            "google": f"https://storage.googleapis.com/ecmwf-open-data/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "azure-scda": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('oper', 'scda')}",
            "azure-waef": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('wave', 'waef')}",
        }
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'
        self.LOCALFILE = f"{self.get_remoteFileName}"


class aifs:
    def template(self):
        self.DESCRIPTION = (
            "ECMWF Open Data - Artificial Inteligence Integrated Forecast System"
        )
        self.DETAILS = {
            "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        }
        self.PRODUCTS = {
            "oper": "operational high-resolution forecast, atmospheric fields",
            "enfo": "ensemble forecast, atmospheric fields",
            "experimental": "experimental high-resolution forecast, atmospheric fields",
        }

        # example file
        # https://data.ecmwf.int/forecasts/20240229/00z/aifs/0p25/oper/20240229000000-0h-oper-fc.grib2

        # Assign correct product suffix
        if not hasattr(self, "get_control"):
            self.get_control = False
        if self.get_control is True:
            product_suffix = "cf"
        else:
            if self.product == "enfo":
                product_suffix = "pf"
            else:
                product_suffix = "fc"

        # AIFS ensembles
        if self.product == "enfo":
            post_root = (
                f"{self.date:%Y%m%d/%Hz}/aifs-ens/0p25/{self.product}"
                f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
            )

        # Operational and experimental runs
        else:
            if self.date >= datetime(2025, 2, 25, 6):
                # ECMWF’s AI forecasts become operational
                # https://www.ecmwf.int/en/about/media-centre/news/2025/ecmwfs-ai-forecasts-become-operational
                post_root = (
                    f"{self.date:%Y%m%d/%Hz}/aifs-single/0p25/{self.product}"
                    f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
                )
            elif self.date >= datetime(2025, 2, 9, 12):
                # Preparing for the operational phase of the AI forecast
                post_root = (
                    f"{self.date:%Y%m%d/%Hz}/aifs-single/0p25/experimental/{self.product}"
                    f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
                )
            else:
                post_root = (
                    f"{self.date:%Y%m%d/%Hz}/aifs/0p25/{self.product}"
                    f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
                )

        self.SOURCES = {
            "google": f"https://storage.googleapis.com/ecmwf-open-data/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
        }
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'
        self.LOCALFILE = f"{self.get_remoteFileName}"

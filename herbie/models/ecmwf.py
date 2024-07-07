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


class ifs:
    def template(self):
        # Allow a user to select the deprecated 0p4-beta resolution,
        # but default to the 0p25 product if resolution is not specified.
        # Sounds like the 0p4-beta product will be deprecated in May 2024.
        if not hasattr(self, "resolution") or self.resolution is None:
            self.resolution = "0p25"
            if self.date < datetime(2024, 2, 1):
                self.resolution = "0p4-beta"

        self.DESCRIPTION = "ECMWF Open Data - Integrated Forecast System"
        self.DETAILS = {
            "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        }
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

        # product suffix
        if self.product in ["enfo", "waef"]:
            product_suffix = "ef"
        else:
            product_suffix = "fc"

        if self.date < datetime(2024, 2, 28, 6):
            post_root = (
                f"{self.date:%Y%m%d/%Hz}/{self.resolution}/{self.product}"
                f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
            )
        else:
            post_root = (
                f"{self.date:%Y%m%d/%Hz}/ifs/{self.resolution}/{self.product}"
                f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
            )

        # If user asks for 'oper' or 'wave', still look for data in scda and waef for the short cut-off high resolution forecast.
        self.SOURCES = {
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "azure-scda": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('oper', 'scda')}",
            "azure-waef": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('wave', 'waef')}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
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
        }

        # example file
        # https://data.ecmwf.int/forecasts/20240229/00z/aifs/0p25/oper/20240229000000-0h-oper-fc.grib2

        product_suffix = "fc"

        post_root = (
            f"{self.date:%Y%m%d/%Hz}/aifs/0p25/{self.product}"
            f"/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"
        )

        self.SOURCES = {
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
        }
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'
        self.LOCALFILE = f"{self.get_remoteFileName}"

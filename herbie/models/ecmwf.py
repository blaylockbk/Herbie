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
    """Template for ECMWF Integrated Forecast System (IFS)."""

    def template(self):
        # --------
        # Metadata
        self.DESCRIPTION = "ECMWF Open Data - Integrated Forecast System"
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'
        self.SOURCE_LINKS = {
            "azure": "",
            "aws": "",
            "ecmwf": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        }

        # ----------
        # Validation

        # IFS is run every 6 hours.
        _hours = range(0, 24, 6)
        if self.date.hour not in _hours:
            raise ValueError(f"Request date's hour must be one of {list(_hours)}")

        # ECMWF provided 0.4 degree data until 2 February 2024 when they
        # started publishing 0.25 degree data. The 0p4-beta product will
        # be deprecated in May 2024.
        _resolutions = ["0p25", "0p4-beta"]
        if not hasattr(self, "resolution") or self.resolution is None:
            self.resolution = "0p25"
            if self.date < datetime(2024, 2, 1):
                self.resolution = "0p4-beta"
        elif self.resolution not in set(_resolutions):
            raise ValueError(f"`resolution` must be one of {list(_resolutions)}")

        # IFS produces the following output products.
        _products = {
            "oper": "operational high-resolution forecast, atmospheric fields",
            "enfo": "ensemble forecast, atmospheric fields",
            "wave": "wave forecasts",
            "waef": "ensemble forecast, ocean wave fields,",
            "scda": "short cut-off high-resolution forecast, atmospheric fields (also known as high-frequency products)",
            "scwv": "short cut-off high-resolution forecast, ocean wave fields (also known as high-frequency products)",
            "mmsf": "multi-model seasonal forecasts fields from the ECMWF model only.",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(f"`product` must be one of {list(_products)}")

        # -----------------
        # Build Source URLs

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

        self.SOURCES = {
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "aws": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",
        }

        # If user asks for 'oper' or 'wave', still look for data in scda
        # and waef for the short cut-off high resolution forecast.
        self.SOURCES |= {
            "azure-scda": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('oper', 'scda')}",
            "azure-waef": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root.replace('wave', 'waef')}",
            "aws-scda": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root.replace('oper', 'scda')}",
            "aws-waef": f"https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/{post_root.replace('wave', 'waef')}",
        }

        self.LOCALFILE = f"{self.get_remoteFileName}"


class aifs:
    """Template for ECMWF Artificial Intelligence Integrated Forecast System (AIFS)."""

    def template(self):
        # --------
        # Metadata
        self.DESCRIPTION = (
            "ECMWF Open Data - Artificial Intelligence Integrated Forecast System"
        )
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = "eccodes"  # 'wgrib2' or 'eccodes'
        self.SOURCE_LINKS = {
            "azure": "",
            "aws": "",
            "ecmwf": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts+from+IFS+and+AIFS",
        }

        # ----------
        # Validation

        # AIFS is run every 6 hours.
        _hours = range(0, 24, 6)
        if self.date.hour not in _hours:
            raise ValueError(f"Request date's hour must be one of {list(_hours)}")

        # AIFS produces the following output products.
        _products = {
            "oper": "operational high-resolution forecast, atmospheric fields",
        }
        self.PRODUCTS = _products
        if not hasattr(self, "product") or self.product is None:
            self.product = list(_products)[0]
        elif self.product not in set(_products):
            raise ValueError(f"`product` must be one of {list(_products)}")

        # -----------------
        # Build Source URLs

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

        self.LOCALFILE = f"{self.get_remoteFileName}"

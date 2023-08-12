## Added by Brian Blaylock
## January 26, 2022

"""
A Herbie template for the ECMWF Open Data GRIB2 files.

See the `media release <https://www.ecmwf.int/en/about/media-centre/news/2022/ecmwf-makes-wide-range-data-openly-available>`_.

- Copyright statement: Copyright "© 2022 European Centre for Medium-Range Weather Forecasts (ECMWF)".
- Source www.ecmwf.int
- License Statement: This data is published under a Creative Commons Attribution 4.0 International (CC BY 4.0). https://creativecommons.org/licenses/by/4.0/
- Disclaimer: ECMWF does not accept any liability whatsoever for any error or omission in the data, their availability, or for any loss or damage arising from their use.

https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts

"""


class ecmwf:
    def template(self):
        # TODO: This will need to be updated someday
        version = "0p4-beta"
        # version = '0p4'

        self.DESCRIPTION = "ECMWF open data"
        self.DETAILS = {
            "ECMWF": "https://confluence.ecmwf.int/display/DAC/ECMWF+open+data%3A+real-time+forecasts",
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
        # https://data.ecmwf.int/forecasts/20220126/00z/0p4-beta/oper/20220126000000-0h-oper-fc.grib2

        # product suffix
        if self.product in ["enfo", "waef"]:
            product_suffix = "ef"
        else:
            product_suffix = "fc"

        post_root = f"{self.date:%Y%m%d/%Hz}/{version}/{self.product}/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2"

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

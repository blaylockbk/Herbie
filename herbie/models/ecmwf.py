## Added by Brian Blaylock
## January 26, 2022

"""
A Herbie template for the ECMWF opendata GRIB2 files.


"""
from datetime import datetime


class ecmwf:
    def template(self):

        version = '0p4-beta'  # this will need to be updated to 0p4 someday
        #version = '0p4'

        self.DESCRIPTION = "ECMWF open data"
        self.DETAILS = {
            "ECMWF": "https://confluence.ecmwf.int/display/UDOC/ECMWF+Open+Data+-+Real+Time",
        }
        self.PRODUCTS = {
            "oper": "operational high-resolution forecast, atmospheric fields",
            "enfo": "ensemble forecast, atmospheric fields",
            "wave": "wave forecasts",
            "waef": "ensemble forecast, ocean wave fields,",
            #"scda": "short cut-off high-resolution forecast, atmospheric fields (also known as high-frequency products)",
            #"scwv": "short cut-off high-resolution forecast, ocean wave fields (also known as high-frequency products)",
            #"mmsf": "multi-model seasonal forecasts fields from the ECMWF model only.",
        }

        # example file
        # https://data.ecmwf.int/forecasts/20220126/00z/0p4-beta/oper/20220126000000-0h-oper-fc.grib2

        # product suffix
        if self.product in ['enfo', 'waef']:
            product_suffix = 'ef'
        else:
            product_suffix = 'fc'

        post_root = f'{self.date:%Y%m%d/%Hz}/{version}/{self.product}/{self.date:%Y%m%d%H%M%S}-{self.fxx}h-{self.product}-{product_suffix}.grib2'

        self.SOURCES = {
            "azure": f"https://ai4edataeuwest.blob.core.windows.net/ecmwf/{post_root}",
            "ecmwf": f"https://data.ecmwf.int/forecasts/{post_root}",

        }
        self.IDX_SUFFIX = [".index"]
        self.IDX_STYLE = 'grib_ls'  # {'wgrib', 'grib_ls'}
        self.LOCALFILE = f"{self.get_remoteFileName}"

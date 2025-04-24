"""
A Herbie template for the HAFS model.
"""

import requests
import re
import functools


class Storms:
    # TODO: This is a little slow 4-6 seconds); at least the caching seems to work.
    def __init__(self):
        pass

    @functools.cached_property
    def id_to_name(self):
        URL = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/"
        messages = set(
            re.findall(
                r"message\d+",
                requests.get(URL).text,
            )
        )

        storms = {}
        for message in messages:
            text = requests.get(URL + message).text
            center, storm_id, storm_name, _ = re.split(r"\s+", text, maxsplit=3)
            storms[storm_id.lower()] = storm_name.lower()
        return storms

    @functools.cached_property
    def name_to_id(self):
        return {v: k for k, v in self.id_to_name.items()}


S = Storms()


class hafsa:
    def template(self):
        self.DESCRIPTION = (
            "Hurricane Analysis and Forecast System (HAFS-A) with GFDL microphysics."
        )
        self.DETAILS = {
            "Homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
            "Hurricane Forecast Improvement Program": "https://hfip.org/hafs",
        }

        if self.storm.isalpha():
            # It looks like the user gave a storm name.
            # Convert that to the storm id.
            self.storm = S.name_to_id.get(self.storm.lower())
            if self.storm is None:
                raise ValueError(f"`storm` should be one of {S.name_to_id.keys()}")

        self.storm_name = S.id_to_name.get(self.storm)

        self.PRODUCTS = {
            "storm.atm": f"{self.storm.upper()}-{self.storm_name.title()}",
            "storm.sat": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.atm": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.sat": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.swath": f"{self.storm.upper()}-{self.storm_name.title()}",
            "ww3": f"{self.storm.upper()}-{self.storm_name.title()}",
        }

        self.flavor = "a"

        PATH = f"hfs{self.flavor}.{self.date:%Y%m%d/%H}/{self.storm}.{self.date:%Y%m%d%H}.hfs{self.flavor}.{self.product}.f{self.fxx:03d}.grb2"

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{PATH}"
        }
        self.IDX_SUFFIX = [".grb2.idx"]
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"


class hafsb:
    # TODO: could clean this up by inheriting from A
    # TODO: and just changing the "flavor"
    def template(self):
        self.DESCRIPTION = (
            "Hurricane Analysis and Forecast System (HAFS-A) with GFDL microphysics."
        )
        self.DETAILS = {
            "Homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
            "Hurricane Forecast Improvement Program": "https://hfip.org/hafs",
        }

        if self.storm.isalpha():
            # It looks like the user gave a storm name.
            # Convert that to the storm id.
            self.storm = S.name_to_id.get(self.storm.lower())
            if self.storm is None:
                raise ValueError(f"`storm` should be one of {S.name_to_id.keys()}")

        self.storm_name = S.id_to_name.get(self.storm)

        self.PRODUCTS = {
            "storm.atm": f"{self.storm.upper()}-{self.storm_name.title()}",
            "storm.sat": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.atm": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.sat": f"{self.storm.upper()}-{self.storm_name.title()}",
            "parent.swath": f"{self.storm.upper()}-{self.storm_name.title()}",
            "ww3": f"{self.storm.upper()}-{self.storm_name.title()}",
        }

        self.flavor = "b"

        PATH = f"hfs{self.flavor}.{self.date:%Y%m%d/%H}/{self.storm}.{self.date:%Y%m%d%H}.hfs{self.flavor}.{self.product}.f{self.fxx:03d}.grb2"

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{PATH}"
        }
        self.IDX_SUFFIX = [".grb2.idx"]
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"

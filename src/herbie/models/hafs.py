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
        base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/"
        storms = {}
        for subdir in ("inphfsb/", "inphfsa/"):
            url = base_url + subdir
            response = requests.get(url)
            if not response.ok:
                continue
            messages = set(re.findall(r"message\d+", response.text))
            for message in messages:
                msg_response = requests.get(url + message)
                if not msg_response.ok:
                    continue
                text = msg_response.text.strip()
                if not text:
                    continue
                parts = re.split(r"\s+", text, maxsplit=3)
                if len(parts) >= 3:
                    _center, storm_id, storm_name = parts[:3]
                    storms[storm_id.lower()] = storm_name.lower()
        return storms

    @functools.cached_property
    def name_to_id(self):
        return {v: k for k, v in self.id_to_name.items()}


S = Storms()


def _configure_storm(template_obj) -> None:
    if not getattr(template_obj, "storm", None):
        raise ValueError(
            "`storm` must be specified for HAFS (e.g., storm='13l' or storm='lee')."
        )

    if template_obj.storm.isalpha():
        # It looks like the user gave a storm name.
        # Convert that to the storm id.
        template_obj.storm = S.name_to_id.get(template_obj.storm.lower())
        if template_obj.storm is None:
            raise ValueError(f"`storm` should be one of {S.name_to_id.keys()}")

    template_obj.storm = template_obj.storm.lower()
    template_obj.storm_name = S.id_to_name.get(template_obj.storm)

    storm_label = (
        f"{template_obj.storm.upper()}-{template_obj.storm_name.title()}"
        if template_obj.storm_name
        else template_obj.storm.upper()
    )

    template_obj.PRODUCTS = {
        "storm.atm": storm_label,
        "storm.sat": storm_label,
        "parent.atm": storm_label,
        "parent.sat": storm_label,
        "parent.swath": storm_label,
        "ww3": storm_label,
    }


class hafsa:
    def template(self):
        self.DESCRIPTION = (
            "Hurricane Analysis and Forecast System (HAFS-A) with GFDL microphysics."
        )
        self.DETAILS = {
            "Homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
            "Hurricane Forecast Improvement Program": "https://hfip.org/hafs",
        }

        _configure_storm(self)

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

        _configure_storm(self)

        self.flavor = "b"

        PATH = f"hfs{self.flavor}.{self.date:%Y%m%d/%H}/{self.storm}.{self.date:%Y%m%d%H}.hfs{self.flavor}.{self.product}.f{self.fxx:03d}.grb2"

        self.SOURCES = {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{PATH}"
        }
        self.IDX_SUFFIX = [".grb2.idx"]
        self.EXPECT_IDX_FILE = "remote"
        self.LOCALFILE = f"{self.get_remoteFileName}"

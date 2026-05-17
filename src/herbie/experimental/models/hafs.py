import functools
import re

import requests

from herbie.experimental.models import ModelTemplate


class StormLookup:
    """Helper class to fetch and cache storm IDs and names from NOAA."""

    def __init__(self):
        pass

    @functools.cached_property
    def id_to_name(self) -> dict[str, str]:
        """Get mapping of storm IDs to storm names."""
        try:
            url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            messages = set(re.findall(r"message\d+", response.text))

            storms = {}
            for message in messages:
                text = requests.get(url + message, timeout=5).text
                parts = re.split(r"\s+", text, maxsplit=3)
                if len(parts) >= 3:
                    storm_id = parts[1].lower()
                    storm_name = parts[2].lower()
                    storms[storm_id] = storm_name
            return storms
        except Exception:
            # Return empty dict if lookup fails
            return {}

    @functools.cached_property
    def name_to_id(self) -> dict[str, str]:
        """Get mapping of storm names to storm IDs."""
        return {v: k for k, v in self.id_to_name.items()}


_STORMS = StormLookup()


class HAFSATemplate(ModelTemplate):
    """Hurricane Analysis and Forecast System (HAFS-A) Model Template."""

    MODEL_NAME = "HAFSA"
    MODEL_DESCRIPTION = "NOAA Hurricane Analysis and Forecast System (HAFS-A)"
    MODEL_WEBSITES = {
        "homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
        "hfip": "https://hfip.org/hafs",
    }

    PARAMS = {
        "storm": {
            "default": None,
            # Note: Valid values are dynamic (fetched from NOAA)
        },
        "product": {
            "default": "storm.atm",
            "valid": [
                "storm.atm",
                "storm.sat",
                "parent.atm",
                "parent.sat",
                "parent.swath",
                "ww3",
            ],
            "descriptions": {
                "storm.atm": "Storm atmospheric fields",
                "storm.sat": "Storm satellite fields",
                "parent.atm": "Parent domain atmospheric fields",
                "parent.sat": "Parent domain satellite fields",
                "parent.swath": "Parent domain swath",
                "ww3": "Wave Watch 3",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 127),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        storm = self.params.get("storm")
        product = self.params.get("product")
        step = self.params.get("step")

        if storm is None:
            raise ValueError("'storm' parameter is required for HAFSA model")

        # Resolve storm name to ID if needed
        if isinstance(storm, str) and storm.isalpha():
            storm_id = _STORMS.name_to_id.get(storm.lower())
            if storm_id is None:
                raise ValueError(
                    f"Storm '{storm}' not found. Available storms: {list(_STORMS.name_to_id.keys())}"
                )
            storm = storm_id

        path = f"hfsa.{date:%Y%m%d/%H}/{storm}.{date:%Y%m%d%H}.hfsa.{product}.f{step:03d}.grb2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{path}",
        }


class HAFSBTemplate(ModelTemplate):
    """Hurricane Analysis and Forecast System (HAFS-B) Model Template."""

    MODEL_NAME = "HAFSB"
    MODEL_DESCRIPTION = "NOAA Hurricane Analysis and Forecast System (HAFS-B)"
    MODEL_WEBSITES = {
        "homepage": "https://wpo.noaa.gov/the-hurricane-analysis-and-forecast-system-hafs/",
        "hfip": "https://hfip.org/hafs",
    }

    PARAMS = {
        "storm": {
            "default": None,
            # Note: Valid values are dynamic (fetched from NOAA)
        },
        "product": {
            "default": "storm.atm",
            "valid": [
                "storm.atm",
                "storm.sat",
                "parent.atm",
                "parent.sat",
                "parent.swath",
                "ww3",
            ],
            "descriptions": {
                "storm.atm": "Storm atmospheric fields",
                "storm.sat": "Storm satellite fields",
                "parent.atm": "Parent domain atmospheric fields",
                "parent.sat": "Parent domain satellite fields",
                "parent.swath": "Parent domain swath",
                "ww3": "Wave Watch 3",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 127),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        storm = self.params.get("storm")
        product = self.params.get("product")
        step = self.params.get("step")

        if storm is None:
            raise ValueError("'storm' parameter is required for HAFSB model")

        # Resolve storm name to ID if needed
        if isinstance(storm, str) and storm.isalpha():
            storm_id = _STORMS.name_to_id.get(storm.lower())
            if storm_id is None:
                raise ValueError(
                    f"Storm '{storm}' not found. Available storms: {list(_STORMS.name_to_id.keys())}"
                )
            storm = storm_id

        path = f"hfsb.{date:%Y%m%d/%H}/{storm}.{date:%Y%m%d%H}.hfsb.{product}.f{step:03d}.grb2"

        return {
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/{path}",
        }

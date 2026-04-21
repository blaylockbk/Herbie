"""
Canadian Meteorological Service (MSC) model templates for Herbie v2.

These models publish one GRIB2 message per file in a web directory,
so inventory is built from directory listings rather than index files.

Models
------
HRDPS  High Resolution Deterministic Prediction System  (2.5-km)
RDPS   Regional Deterministic Prediction System         (10-km)
GDPS   Global Deterministic Prediction System           (15-km)

Data: https://dd.weather.gc.ca/
License: https://eccc-msc.github.io/open-data/licence/readme_en/
"""

from __future__ import annotations

import re

from herbie.v2._base import HerbieModel
from herbie.v2._sources import DirectorySource


def _parse_msc_filename(fname: str) -> dict:
    """
    Extract metadata from an MSC GRIB2 filename.

    Example::
        20240615T00Z_MSC_HRDPS_TMP_AGL-2m_RLatLon0.0225_PT006H.grib2
    """
    meta: dict = {}
    # Step / forecast hour
    m = re.search(r"_PT(\d+)H", fname)
    if m:
        meta["fxx"] = int(m.group(1))
    # Resolution
    m = re.search(r"_RLatLon([.\d]+)_", fname)
    if m:
        meta["resolution"] = m.group(1)
    return meta


class HRDPS(HerbieModel):
    """
    Canadian High Resolution Deterministic Prediction System (HRDPS).

    2.5-km deterministic model over a continental or north domain.
    Data available for the last ~24 hours from the MSC Datamart.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours (0–48).
    product : {'continental', 'north'}, default 'continental'
        Domain:

        ``'continental'``  Continental Canada + CONUS border, 2.5-km.
        ``'north'``        Northern domain, 3-km.

    Notes
    -----
    Unlike NOAA models, each GRIB2 file contains a single variable/level
    combination.  ``H.inventory()`` lists *all* available files in the
    directory; use Polars expressions to filter by variable and level
    before calling ``H.download()``.

    References
    ----------
    * https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/readme_hrdps-datamart_en/
    """

    MODEL_NAME = "HRDPS"
    MODEL_DESCRIPTION = "Canadian High Resolution Deterministic Prediction System"
    MODEL_WEBSITES = {
        "Datamart": "https://eccc-msc.github.io/open-data/msc-data/nwp_hrdps/",
        "Data": "https://dd.weather.gc.ca/model_hrdps/",
    }
    SOURCE_TYPE = "directory"

    PARAMS = {
        "product": {
            "default": "continental",
            "valid": ["continental", "north"],
            "descriptions": {
                "continental": "Continental domain; 2.5-km resolution",
                "north":       "Northern domain; 3-km resolution",
            },
        },
    }

    _RES = {"continental": "2.5km", "north": "3km"}
    _GRID = {"continental": "RLatLon0.0225", "north": "RLatLon0.03"}
    _TAG = {"continental": "HRDPS", "north": "HRDPS-North"}

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        res = self._RES[product]
        base = (
            f"https://dd.weather.gc.ca/{d:%Y%m%d}/WXO-DD/"
            f"model_hrdps/{product}/{res}/{d:%H}/{fxx:03d}/"
        )

        tag = self._TAG[product]
        pattern = (
            rf"(?P<filename>{re.escape(f'{d:%Y%m%dT%HZ}_MSC_{tag}_')}"
            rf"(?P<variable>\w+)_(?P<level>[\w.\-]+)_"
            rf"{re.escape(self._GRID[product])}_PT{fxx:03d}H\.grib2)"
        )

        return {
            "msc": DirectorySource(
                url=base,
                file_pattern=pattern,
                parse_metadata=_parse_msc_filename,
            )
        }


class RDPS(HerbieModel):
    """
    Canadian Regional Deterministic Prediction System (RDPS).

    10-km deterministic regional model.
    Data available for the last ~24 hours from the MSC Datamart.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours (0–84).

    References
    ----------
    * https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/readme_rdps-datamart_en/
    """

    MODEL_NAME = "RDPS"
    MODEL_DESCRIPTION = "Canadian Regional Deterministic Prediction System"
    MODEL_WEBSITES = {
        "Datamart": "https://eccc-msc.github.io/open-data/msc-data/nwp_rdps/",
    }
    SOURCE_TYPE = "directory"

    PARAMS = {}

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        base = (
            f"https://dd.weather.gc.ca/{d:%Y%m%d}/WXO-DD/"
            f"model_rdps/10km/{d:%H}/{fxx:03d}/"
        )
        pattern = (
            rf"(?P<filename>{re.escape(f'{d:%Y%m%dT%HZ}_MSC_RDPS_')}"
            rf"(?P<variable>\w+)_(?P<level>[\w.\-]+)_"
            rf"RLatLon0\.09_PT{fxx:03d}H\.grib2)"
        )
        return {
            "msc": DirectorySource(
                url=base,
                file_pattern=pattern,
                parse_metadata=_parse_msc_filename,
            )
        }


class GDPS(HerbieModel):
    """
    Canadian Global Deterministic Prediction System (GDPS).

    15-km deterministic global model.
    Data available for the last ~24 hours from the MSC Datamart.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours (0–240).

    References
    ----------
    * https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/readme_gdps-datamart_en/
    """

    MODEL_NAME = "GDPS"
    MODEL_DESCRIPTION = "Canadian Global Deterministic Prediction System"
    MODEL_WEBSITES = {
        "Datamart": "https://eccc-msc.github.io/open-data/msc-data/nwp_gdps/",
    }
    SOURCE_TYPE = "directory"

    PARAMS = {}

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        base = (
            f"https://dd.weather.gc.ca/model_gem_global/15km/grib2/lat_lon/"
            f"{d:%H}/{fxx:03d}/"
        )
        pattern = (
            rf"(?P<filename>CMC_glb_(?P<variable>\w+)_(?P<level>[\w.\-]+)_"
            rf"latlon\.15x\.15_{d:%Y%m%d%H}_P{fxx:03d}\.grib2)"
        )
        return {
            "msc": DirectorySource(
                url=base,
                file_pattern=pattern,
                parse_metadata=_parse_msc_filename,
            )
        }

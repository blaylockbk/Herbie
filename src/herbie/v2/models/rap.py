"""RAP, RAP-Historical, and RAP-NCEI model templates for Herbie v2."""

from __future__ import annotations

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource


class RAP(HerbieModel):
    """
    NOAA Rapid Refresh (RAP).

    13-km hourly mesoscale model covering North America.  Initialized
    every hour with forecasts to 21 h (51 h for the 03 and 15 UTC
    cycles).

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int or str, default 0
        Forecast lead time in hours (0–21, or 0–51 for 03/15Z).
    product : str, default 'awp130pgrb'
        Output grid and level type:

        ``'awp130pgrb'``  CONUS pressure levels; 13-km.
        ``'awp252pgrb'``  CONUS pressure levels; 20-km.
        ``'wrfprs'``      Full domain pressure levels; 13-km.
        ``'wrfnat'``      Full domain native levels; 13-km.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/rap/
    * https://registry.opendata.aws/noaa-rap/
    """

    MODEL_NAME = "RAP"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh — CONUS"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/rap/",
        "AWS": "https://registry.opendata.aws/noaa-rap/",
    }

    PARAMS = {
        "product": {
            "default": "awp130pgrb",
            "valid": [
                "awp130pgrb",
                "awp252pgrb",
                "awp236pgrb",
                "awp130bgrb",
                "awp252bgrb",
                "wrfprs",
                "wrfnat",
                "awip32",
                "awp242",
                "awp200",
                "awp243",
                "wrfmsl",
            ],
            "descriptions": {
                "awp130pgrb": "CONUS pressure levels; 13-km resolution",
                "awp252pgrb": "CONUS pressure levels; 20-km resolution",
                "awp236pgrb": "CONUS pressure levels; 40-km resolution",
                "awp130bgrb": "CONUS native levels; 13-km resolution",
                "awp252bgrb": "CONUS native levels; 20-km resolution",
                "wrfprs": "Full domain pressure levels; 13-km",
                "wrfnat": "Full domain native levels; 13-km",
                "awip32": "North American Master Grid; 32-km",
                "awp242": "Alaska quadruple resolution; 11-km",
                "awp200": "Puerto Rico pressure levels; 16-km",
                "awp243": "Eastern North America; 0.4°",
                "wrfmsl": "WRFMSL; 13-km",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]

        path = f"rap.{d:%Y%m%d}/rap.t{d:%H}z.{product}f{fxx:02d}.grib2"
        idx = [".idx", ".grib2.idx"]
        return {
            "aws": GribSource(f"https://noaa-rap-pds.s3.amazonaws.com/{path}", idx),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rap/prod/{path}", idx
            ),
            "google": GribSource(
                f"https://storage.googleapis.com/rapid-refresh/{path}", idx
            ),
            "azure": GribSource(
                f"https://noaarap.blob.core.windows.net/rap/{path}", idx
            ),
        }


class RAPHistorical(HerbieModel):
    """
    NOAA RAP / RUC Historical Archive at NCEI.

    Covers 2012–present (RAP) and pre-2012 (RUC).  Multiple grids
    are available; all are tried in source-priority order.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours.
    product : {'analysis', 'forecast'}, default 'analysis'

    References
    ----------
    * https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update
    """

    MODEL_NAME = "RAPHistorical"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh — NCEI Historical"
    MODEL_WEBSITES = {
        "NCEI": "https://www.ncei.noaa.gov/products/weather-climate-models/rapid-refresh-update",
    }

    PARAMS = {
        "product": {
            "default": "analysis",
            "valid": ["analysis", "forecast"],
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        base = (
            f"https://www.ncei.noaa.gov/data/rapid-refresh/access/historical/{product}"
        )
        idx = [".inv", ".grb2.inv", ".grb.inv"]
        return {
            "rap_130": GribSource(
                f"{base}/{d:%Y%m/%Y%m%d}/rap_130_{d:%Y%m%d_%H%M}_{fxx:03d}.grb2", idx
            ),
            "rap_252": GribSource(
                f"{base}/{d:%Y%m/%Y%m%d}/rap_252_{d:%Y%m%d_%H%M}_{fxx:03d}.grb2", idx
            ),
            "ruc_252": GribSource(
                f"{base}/{d:%Y%m/%Y%m%d}/ruc2_252_{d:%Y%m%d_%H%M}_{fxx:03d}.grb", idx
            ),
        }

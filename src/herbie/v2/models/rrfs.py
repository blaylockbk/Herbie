"""
Rapid Refresh Forecast System (RRFS) and
RRFS Ensemble Forecast System (REFS) Model Templates.

RRFS and REFS replace NAM, HREF, SREF, and HiresW effective August 31, 2026
(1200 UTC). Pre-implementation data on NOMADS starting ~June 9, 2026.

Classes
-------
RRFSTemplate       Deterministic RRFS — CONUS, Alaska, Hawaii, Puerto Rico
RRFSFireWxTemplate Deterministic RRFS — relocatable 1.5 km fire weather domain
REFSTemplate       RRFS Ensemble Forecast System (ensemble products)

References
----------
* https://www.nco.ncep.noaa.gov/pmb/products/rrfs/
* https://www.weather.gov/media/notification/pdf_2026/scn26-48_RRFS_and_REFS_Implementation.pdf
"""

from datetime import datetime

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource

# Operational implementation date: 1200 UTC August 31, 2026.
# Files before this date live under .../rrfs/para/ (or refs/para/);
# files on or after live under .../rrfs/prod/ (or refs/prod/).
_RRFS_IMPL_DATE = datetime(2026, 8, 31, 12)

# Resolution string keyed by domain (used in filenames).
_DOMAIN_RESOLUTION = {
    "conus": "3km",
    "ak": "3km",
    "hi": "2p5km",
    "pr": "2p5km",
}


class RRFS(HerbieModel):
    """
    Rapid Refresh Forecast System (RRFS) — Deterministic.

    3 km resolution for CONUS and Alaska; 2.5 km for Hawaii and Puerto Rico.
    Runs every hour; extended to 84 h for 00/06/12/18 UTC cycles and to 18 h
    for all other hourly cycles.

    Replaces NAM and HiresW (except Guam) effective August 31, 2026.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours.
        Max 84 h for 00/06/12/18z cycles; max 18 h for all other cycles.
    product : {'prslev', '2dfld', 'subh'}, default 'prslev'
        Output product type.
    domain : {'conus', 'ak', 'hi', 'pr'}, default 'conus'
        Output domain / grid.

    Notes
    -----
    AWS, Google, and Azure bucket names are not yet officially confirmed;
    the names used here follow the convention of similar NOAA model buckets
    and should be verified once the data goes live.
    """

    MODEL_NAME = "RRFS"
    MODEL_DESCRIPTION = "Rapid Refresh Forecast System"
    MODEL_WEBSITES = {
        "NCEP": "https://www.nco.ncep.noaa.gov/pmb/products/rrfs/",
        "NOAA GSL": "https://rapidrefresh.noaa.gov/hrrr/",
        "scn": "https://www.weather.gov/media/notification/pdf_2026/scn26-48_RRFS_and_REFS_Implementation.pdf",
    }

    PARAMS = {
        "product": {
            "default": "prslev",
            "valid": ["prslev", "2dfld", "subh"],
            "aliases": {
                "prs": "prslev",
                "pressure": "prslev",
                "sfc": "2dfld",
                "surface": "2dfld",
                "2d": "2dfld",
                "subhourly": "subh",
            },
            "descriptions": {
                "prslev": "3D pressure-level fields",
                "2dfld": "2D surface and diagnostic fields",
                "subh": "2D surface fields — sub-hourly output (15/30/45 min within each hour)",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "pr"],
            "aliases": {
                "alaska": "ak",
                "hawaii": "hi",
                "puerto_rico": "pr",
            },
            "descriptions": {
                "conus": "Contiguous US — Lambert Conformal 3 km (1799×1059)",
                "ak": "Alaska — Polar Stereographic 3 km (1649×1105)",
                "hi": "Hawaii — Mercator 2.5 km (321×225)",
                "pr": "Puerto Rico — Mercator 2.5 km (544×310)",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 85),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def _build_sources(self) -> dict:
        d = self.date
        step = self.params["step"]
        product = self.params["product"]
        domain = self.params["domain"]

        res = _DOMAIN_RESOLUTION[domain]

        # Build filename based on product type:
        #   prslev: rrfs.tCCz.prslev.{res}.fFFF.{domain}.grib2
        #   2dfld:  rrfs.tCCz.2dfld.{res}.fFFF.{domain}.grib2
        #   subh:   rrfs.tCCz.2dfld.{res}.subh.fFFF.{domain}.grib2
        if product == "prslev":
            fname = f"rrfs.t{d:%H}z.prslev.{res}.f{step:03d}.{domain}.grib2"
        elif product == "2dfld":
            fname = f"rrfs.t{d:%H}z.2dfld.{res}.f{step:03d}.{domain}.grib2"
        elif product == "subh":
            fname = f"rrfs.t{d:%H}z.2dfld.{res}.subh.f{step:03d}.{domain}.grib2"

        stage = "prod" if d >= _RRFS_IMPL_DATE else "para"
        dirpath = f"rrfs.{d:%Y%m%d}/{d:%H}"
        path = f"{dirpath}/{fname}"

        idx = [".idx", ".grib2.idx"]
        nomads_base = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/{stage}"

        return {
            "nomads": GribSource(f"{nomads_base}/{path}", idx),
            "aws": GribSource(f"https://noaa-rrfs-pds.s3.amazonaws.com/{path}", idx),
            "google": GribSource(
                f"https://storage.googleapis.com/rapid-refresh-forecast-system/{path}",
                idx,
            ),
            "azure": GribSource(
                f"https://noaarrfs.blob.core.windows.net/rrfs/{path}", idx
            ),
        }

    def get_remote_urls(self) -> dict[str, str]:
        """Return remote URLs as a plain dict (required by HerbieModel ABC)."""
        return {k: v.url for k, v in self._build_sources().items()}


class RRFSFireWx(HerbieModel):
    """
    Rapid Refresh Forecast System — Fire Weather (RRFS-FireWx).

    A relocatable 1.5 km run over a 5×5-degree rotated lat-lon region.
    Grid location and exact dimensions vary by cycle (~561×354).
    No sub-hourly output for this domain.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours.
    product : {'prslev', '2dfld'}, default '2dfld'
        Output product type.

    Notes
    -----
    Fire weather files use a separate ``firewx.YYYYMMDD/CC/`` directory,
    distinct from the main ``rrfs.YYYYMMDD/CC/`` layout.
    """

    MODEL_NAME = "RRFS_FIREWX"
    MODEL_DESCRIPTION = "Rapid Refresh Forecast System — Fire Weather"
    MODEL_WEBSITES = {
        "ncep": "https://www.nco.ncep.noaa.gov/pmb/products/rrfs/",
    }

    PARAMS = {
        "product": {
            "default": "2dfld",
            "valid": ["prslev", "2dfld"],
            "aliases": {
                "prs": "prslev",
                "pressure": "prslev",
                "sfc": "2dfld",
                "surface": "2dfld",
                "2d": "2dfld",
            },
            "descriptions": {
                "prslev": "3D pressure-level fields — 1.5 km",
                "2dfld": "2D surface and diagnostic fields — 1.5 km",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 85),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def _build_sources(self) -> dict:
        d = self.date
        step = self.params["step"]
        product = self.params["product"]

        # firewx.YYYYMMDD/CC/rrfs.tCCz.{product}.1p5km.fFFF.firewx_lcc.grib2
        fname = f"rrfs.t{d:%H}z.{product}.1p5km.f{step:03d}.firewx_lcc.grib2"

        stage = "prod" if d >= _RRFS_IMPL_DATE else "para"
        dirpath = f"firewx.{d:%Y%m%d}/{d:%H}"
        path = f"{dirpath}/{fname}"

        idx = [".idx", ".grib2.idx"]
        nomads_base = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/{stage}"

        return {
            "nomads": GribSource(f"{nomads_base}/{path}", idx),
            "aws": GribSource(f"https://noaa-rrfs-pds.s3.amazonaws.com/{path}", idx),
            "google": GribSource(
                f"https://storage.googleapis.com/rapid-refresh-forecast-system/{path}",
                idx,
            ),
            "azure": GribSource(
                f"https://noaarrfs.blob.core.windows.net/rrfs/{path}", idx
            ),
        }

    def get_remote_urls(self) -> dict[str, str]:
        """Return remote URLs as a plain dict (required by HerbieModel ABC)."""
        return {k: v.url for k, v in self._build_sources().items()}


class REFS(HerbieModel):
    """
    RRFS Ensemble Forecast System (REFS).

    Combines RRFS deterministic and ensemble members (plus HRRR members for
    CONUS/AK) to produce ensemble products. Runs to 60 h for 00/06/12/18 UTC
    cycles only. Replaces HREF effective August 31, 2026.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC). Must be 00/06/12/18z.
    step : int, default 0
        Forecast lead time in hours (0–60).
    product : {'mean', 'sprd', 'pmmn', 'lpmm', 'avrg', 'prob', 'eas', 'ffri'}
        Ensemble product type. ``ffri`` is CONUS-only.
    domain : {'conus', 'ak', 'hi', 'pr'}, default 'conus'
        Output domain.

    Notes
    -----
    REFS files use a separate ``refs/`` directory hierarchy on NOMADS,
    distinct from the ``rrfs/`` hierarchy used by the deterministic system.
    Step is formatted as 2-digit ``fFF`` (vs. 3-digit ``fFFF`` for RRFS).
    """

    MODEL_NAME = "REFS"
    MODEL_DESCRIPTION = "RRFS Ensemble Forecast System"
    MODEL_WEBSITES = {
        "ncep": "https://www.nco.ncep.noaa.gov/pmb/products/refs/",
        "NOAA GSL": "https://rapidrefresh.noaa.gov/hrrr/",
        "scn": "https://www.weather.gov/media/notification/pdf_2026/scn26-48_RRFS_and_REFS_Implementation.pdf",
    }

    PARAMS = {
        "product": {
            "default": "mean",
            "valid": ["mean", "sprd", "pmmn", "lpmm", "avrg", "prob", "eas", "ffri"],
            "aliases": {
                "average": "mean",
                "spread": "sprd",
                "prob_matched": "pmmn",
                "local_prob_matched": "lpmm",
                "flash_flood": "ffri",
            },
            "descriptions": {
                "mean": "Simple ensemble mean",
                "sprd": "Ensemble spread",
                "pmmn": "Probability-matched mean (full domain)",
                "lpmm": "Localized probability-matched mean",
                "avrg": "Combination of pmmn and mean fields",
                "prob": "Probabilistic output (% of members meeting threshold)",
                "eas": "Ensemble Agreement Scale probabilistic output",
                "ffri": "Flash flood and recurrence interval exceedance (CONUS only)",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "pr"],
            "aliases": {
                "alaska": "ak",
                "hawaii": "hi",
                "puerto_rico": "pr",
                "puertorico": "pr",
            },
            "descriptions": {
                "conus": "Contiguous US",
                "ak": "Alaska",
                "hi": "Hawaii",
                "pr": "Puerto Rico",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 61),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def _validate_params(self) -> None:
        """Extended validation: ffri is only available for the conus domain."""
        super()._validate_params()
        if (
            self.params.get("product") == "ffri"
            and self.params.get("domain") != "conus"
        ):
            raise ValueError(
                f"The 'ffri' product is only available for domain='conus', "
                f"got domain='{self.params.get('domain')}'."
            )

    def _build_sources(self) -> dict:
        d = self.date
        step = self.params["step"]
        product = self.params["product"]
        domain = self.params["domain"]

        # refs.YYYYMMDD/CC/ensprod/refs.tCCz.{type}.fFF.{dom}.grib2
        # Note: REFS uses 2-digit step (fFF), unlike RRFS deterministic (fFFF).
        fname = f"refs.t{d:%H}z.{product}.f{step:02d}.{domain}.grib2"

        stage = "prod" if d >= _RRFS_IMPL_DATE else "para"
        # REFS lives under refs/ not rrfs/ on NOMADS.
        dirpath = f"refs.{d:%Y%m%d}/{d:%H}/ensprod"
        path = f"{dirpath}/{fname}"

        idx = [".idx", ".grib2.idx"]
        nomads_base = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/refs/{stage}"

        return {
            "nomads": GribSource(f"{nomads_base}/{path}", idx),
            "aws": GribSource(f"https://noaa-rrfs-pds.s3.amazonaws.com/{path}", idx),
            "google": GribSource(
                f"https://storage.googleapis.com/rapid-refresh-forecast-system/{path}",
                idx,
            ),
            "azure": GribSource(
                f"https://noaarrfs.blob.core.windows.net/rrfs/{path}", idx
            ),
        }

    def get_remote_urls(self) -> dict[str, str]:
        """Return remote URLs as a plain dict (required by HerbieModel ABC)."""
        return {k: v.url for k, v in self._build_sources().items()}

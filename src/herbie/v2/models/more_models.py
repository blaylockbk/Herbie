"""Additional NOAA model templates for Herbie v2."""

from __future__ import annotations

from datetime import datetime

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource


# ---------------------------------------------------------------------------
# NBM QMD
# ---------------------------------------------------------------------------


class NBMQMD(HerbieModel):
    """
    NOAA National Blend of Models — Quantile Mapping Downscaling (QMD).

    Parameters
    ----------
    date : str or datetime
        Model cycle datetime (UTC).
    fxx : int, default 1
        Forecast lead time in hours (1–214).
    product : {'co', 'ak', 'hi', 'gu', 'pr'}, default 'co'
        Domain (same as NBM).
    """

    MODEL_NAME = "NBMQMD"
    MODEL_DESCRIPTION = "NOAA National Blend of Models — QMD"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
        "AWS": "https://registry.opendata.aws/noaa-nbm/",
    }

    PARAMS = {
        "product": {
            "default": "co",
            "valid": ["co", "ak", "hi", "gu", "pr"],
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = max(self.fxx, 1)
        product = self.params["product"]
        path = f"blend.{d:%Y%m%d/%H}/qmd/blend.t{d:%H}z.qmd.f{fxx:03d}.{product}.grib2"
        idx = [".idx", ".grib2.idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/blend/prod/{path}", idx
            ),
            "aws": GribSource(
                f"https://noaa-nbm-grib2-pds.s3.amazonaws.com/{path}", idx
            ),
        }


# ---------------------------------------------------------------------------
# HREF
# ---------------------------------------------------------------------------


class HREF(HerbieModel):
    """
    NOAA High-Resolution Ensemble Forecast (HREF).

    ~3-km ensemble blending HRRR, NAM, and HiResW members.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
        Runs at 00/12Z (CONUS + Hawaii) and 06/18Z (CONUS + Alaska + PR).
    fxx : int, default 0
        Forecast lead time in hours (0–48).
    product : str, default 'mean'
        Ensemble product:

        ``'mean'``  Arithmetic mean of all members.
        ``'pmmn'``  Probability-matched mean (full domain).
        ``'lpmm'``  Localised probability-matched mean.
        ``'sprd'``  Ensemble spread.
        ``'prob'``  Probabilistic output.
        ``'eas'``   Ensemble Agreement Scale probability.
        ``'avrg'``  Average of mean and pmmn (precipitation only).

    domain : {'conus', 'ak', 'hi', 'pr'}, default 'conus'

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/href/
    """

    MODEL_NAME = "HREF"
    MODEL_DESCRIPTION = "NOAA High-Resolution Ensemble Forecast"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/href/",
    }

    PARAMS = {
        "product": {
            "default": "mean",
            "valid": ["mean", "pmmn", "lpmm", "avrg", "sprd", "prob", "eas"],
            "descriptions": {
                "mean": "Arithmetic mean of all members",
                "pmmn": "Probability-matched mean (full domain)",
                "lpmm": "Localised probability-matched mean",
                "avrg": "Average of mean and pmmn (precipitation only)",
                "sprd": "Ensemble spread",
                "prob": "Probabilistic output",
                "eas": "Ensemble Agreement Scale probability",
            },
        },
        "domain": {
            "default": "conus",
            "valid": ["conus", "ak", "hi", "pr"],
            "aliases": {"alaska": "ak", "hawaii": "hi", "puertorico": "pr"},
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        domain = self.params["domain"]
        path = (
            f"href.{d:%Y%m%d}/ensprod/href.t{d:%H}z.{domain}.{product}.f{fxx:02d}.grib2"
        )
        idx = [".grib2.idx", ".idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/href/prod/{path}", idx
            ),
        }


# ---------------------------------------------------------------------------
# CFS
# ---------------------------------------------------------------------------


class CFS(HerbieModel):
    """
    NOAA Climate Forecast System (CFS).

    Seasonal forecast model at ~100-km resolution.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours.
    product : {'time_series', '6_hourly', 'monthly_means'}, default '6_hourly'

    member : int, default 1
        Ensemble member (1–4).

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/cfs/
    * https://registry.opendata.aws/noaa-cfs/
    """

    MODEL_NAME = "CFS"
    MODEL_DESCRIPTION = "NOAA Climate Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/cfs/",
        "AWS": "https://registry.opendata.aws/noaa-cfs/",
    }

    PARAMS = {
        "product": {
            "default": "6_hourly",
            "valid": ["time_series", "6_hourly", "monthly_means"],
            "descriptions": {
                "time_series": "CFS daily-mean time series (single variable per file)",
                "6_hourly": "CFS 6-hourly gridded output",
                "monthly_means": "CFS monthly-mean output",
            },
        },
        "member": {
            "default": 1,
            "valid": [1, 2, 3, 4],
        },
        "kind": {
            "default": "pgbf",
            "valid": ["flxf", "pgbf", "ocnh", "ocnf", "ipvf"],
            "descriptions": {
                "flxf": "Surface / radiative fluxes",
                "pgbf": "3D pressure-level fields, 1°",
                "ocnh": "3D ocean data, 0.5°",
                "ocnf": "3D ocean data, 1°",
                "ipvf": "3D isentropic-level fields, 1°",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        member = self.params["member"]
        kind = self.params.get("kind", "pgbf")

        idx = [".grb2.idx", ".idx"]

        if product == "time_series":
            variable = self.params.get("variable", "tmp2m")
            post = (
                f"cfs.{d:%Y%m%d/%H}/time_grib_{member:02d}/"
                f"{variable}.{member:02d}.{d:%Y%m%d%H}.daily.grb2"
            )
        elif product == "6_hourly":
            valid = self.valid_date
            post = (
                f"cfs.{d:%Y%m%d/%H}/6hrly_grib_{member:02d}/"
                f"{kind}{valid:%Y%m%d%H}.{member:02d}.{d:%Y%m%d%H}.grb2"
            )
        else:  # monthly_means
            import calendar
            from datetime import timedelta

            month_offset = self.params.get("month", 1)
            # approximate: advance ~30 days per month
            valid_month = d + timedelta(days=30 * month_offset - 1)
            hour = self.params.get("hour")
            if hour is None:
                post = (
                    f"cfs.{d:%Y%m%d/%H}/monthly_grib_{member:02d}/"
                    f"{kind}.{member:02d}.{d:%Y%m%d%H}.{valid_month:%Y%m}.avrg.grib.grb2"
                )
            else:
                post = (
                    f"cfs.{d:%Y%m%d/%H}/monthly_grib_{member:02d}/"
                    f"{kind}.{member:02d}.{d:%Y%m%d%H}.{valid_month:%Y%m}.avrg.grib.{hour:02d}Z.grb2"
                )

        return {
            "aws": GribSource(f"https://noaa-cfs-pds.s3.amazonaws.com/{post}", idx),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post}", idx
            ),
        }


# ---------------------------------------------------------------------------
# AIGFS  (AI Global Forecast System)
# ---------------------------------------------------------------------------


class AIGFS(HerbieModel):
    """
    NOAA AI Global Forecast System (AIGFS).

    Machine-learning global NWP at 0.25° resolution.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours.
    product : {'sfc', 'pres'}, default 'sfc'
        Surface or pressure-level fields.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/aigfs/
    """

    MODEL_NAME = "AIGFS"
    MODEL_DESCRIPTION = "NOAA AI Global Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/aigfs/",
    }

    PARAMS = {
        "product": {
            "default": "sfc",
            "valid": ["sfc", "pres"],
            "aliases": {"surface": "sfc", "pressure": "pres"},
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        path = (
            f"aigfs.{d:%Y%m%d/%H}/model/atmos/grib2/"
            f"aigfs.t{d:%H}z.{product}.f{fxx:03d}.grib2"
        )
        idx = [".grib2.idx", ".idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/aigfs/prod/{path}", idx
            ),
        }


# ---------------------------------------------------------------------------
# HGEFS  (Hybrid Global Ensemble Forecast System)
# ---------------------------------------------------------------------------


class HGEFS(HerbieModel):
    """
    NOAA Hybrid Global Ensemble Forecast System (HGEFS).

    Blends AI and physics-based ensemble output.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    fxx : int, default 0
        Forecast lead time in hours (0–384).
    product : {'pres', 'sfc'}, default 'pres'
    member : {'spr', 'avg'}, default 'spr'
        Ensemble statistic.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/hgefs/
    """

    MODEL_NAME = "HGEFS"
    MODEL_DESCRIPTION = "NOAA Hybrid Global Ensemble Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/hgefs/",
    }

    PARAMS = {
        "product": {
            "default": "pres",
            "valid": ["pres", "sfc"],
            "aliases": {"pressure": "pres", "surface": "sfc"},
        },
        "member": {
            "default": "spr",
            "valid": ["spr", "avg"],
            "descriptions": {"spr": "Ensemble spread", "avg": "Ensemble average"},
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        fxx = self.fxx
        product = self.params["product"]
        member = self.params["member"]
        path = (
            f"hgefs.{d:%Y%m%d/%H}/ensstat/products/atmos/grib2/"
            f"hgefs.t{d:%H}z.{product}.{member}.f{fxx:03d}.grib2"
        )
        idx = [".grib2.idx"]
        return {
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hgefs/prod/{path}", idx
            ),
        }

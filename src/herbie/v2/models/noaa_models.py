"""NAM, NBM, GEFS, and RRFS model templates for Herbie v2."""

from __future__ import annotations

from datetime import datetime

from herbie.v2._base import HerbieModel
from herbie.v2._sources import GribSource


# ---------------------------------------------------------------------------
# NAM
# ---------------------------------------------------------------------------


class NAM(HerbieModel):
    """
    NOAA North America Mesoscale (NAM) model.

    Multiple domains and resolutions available.  Initialized four times
    daily (00, 06, 12, 18 UTC) with forecasts to 60 h.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–60).
    product : str, default 'conusnest.hiresf'
        Output domain and type.  Key options:

        ``'conusnest.hiresf'``    CONUS 5-km.
        ``'firewxnest.hiresf'``   Fire Weather 1.33-km.
        ``'alaskanest.hiresf'``   Alaska 6-km.
        ``'awphys'``              NAM 218 AWIPS Grid 12-km (pressure levels).
        ``'awip12'``              NAM 218 AWIPS Grid 12-km (surface fields).

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/nam/
    """

    MODEL_NAME = "NAM"
    MODEL_DESCRIPTION = "NOAA North America Mesoscale Model"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/nam/",
        "AWS": "https://registry.opendata.aws/noaa-nam/",
    }

    PARAMS = {
        "product": {
            "default": "conusnest.hiresf",
            "valid": [
                "conusnest.hiresf",
                "firewxnest.hiresf",
                "alaskanest.hiresf",
                "hawaiinest.hiresf",
                "priconest.hiresf",
                "afwaca",
                "awphys",
                "awip12",
                "goes218",
                "bgrdsf",
                "bgrd3d",
                "awip32",
            ],
            "descriptions": {
                "conusnest.hiresf": "CONUS 5-km",
                "firewxnest.hiresf": "Fire Weather 1.33-km CONUS / 1.5-km Alaska",
                "alaskanest.hiresf": "Alaska 6-km",
                "hawaiinest.hiresf": "Hawaii 6-km",
                "priconest.hiresf": "Puerto Rico 3-km",
                "awphys": "CONUS 12-km; pressure-level fields",
                "awip12": "CONUS 12-km; surface fields",
                "awip32": "North American Master Grid 32-km",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]
        path = f"nam.{d:%Y%m%d}/nam.t{d:%H}z.{product}{step:02d}.tm00.grib2"
        idx = [".idx", ".grib2.idx"]
        return {
            "aws": GribSource(f"https://noaa-nam-pds.s3.amazonaws.com/{path}", idx),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/nam/prod/{path}", idx
            ),
        }


# ---------------------------------------------------------------------------
# NBM
# ---------------------------------------------------------------------------


class NBM(HerbieModel):
    """
    NOAA National Blend of Models (NBM).

    Calibrated probabilistic guidance blending multiple NWP models
    and MOS.  Available at 13-km resolution.

    Parameters
    ----------
    date : str or datetime
        Model cycle datetime (UTC).
    step : int, default 1
        Forecast lead time in hours (1–214).  Note: step=0 is not provided.
    product : {'co', 'ak', 'hi', 'gu', 'pr'}, default 'co'
        Domain:

        ``'co'``  CONUS; 13-km.
        ``'ak'``  Alaska; 13-km.
        ``'hi'``  Hawaii; 13-km.
        ``'gu'``  Guam; 13-km.
        ``'pr'``  Puerto Rico; 13-km.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/blend/
    * https://registry.opendata.aws/noaa-nbm/
    """

    MODEL_NAME = "NBM"
    MODEL_DESCRIPTION = "NOAA National Blend of Models"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/blend/",
        "AWS": "https://registry.opendata.aws/noaa-nbm/",
        "NWS": "https://www.weather.gov/mdl/nbm_home",
    }

    PARAMS = {
        "product": {
            "default": "co",
            "valid": ["co", "ak", "hi", "gu", "pr"],
            "descriptions": {
                "co": "CONUS 13-km",
                "ak": "Alaska 13-km",
                "hi": "Hawaii 13-km",
                "gu": "Guam 13-km",
                "pr": "Puerto Rico 13-km",
            },
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        # step=0 is not provided by NBM; silently floor to 1
        step = max(self.step, 1)
        product = self.params["product"]
        path = (
            f"blend.{d:%Y%m%d/%H}/core/blend.t{d:%H}z.core.f{step:03d}.{product}.grib2"
        )
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
# GEFS
# ---------------------------------------------------------------------------


class GEFS(HerbieModel):
    """
    NOAA Global Ensemble Forecast System (GEFS).

    20–31 member ensemble.  Available since 2017 on AWS.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–384).
    product : str, default 'atmos.5'
        Output grid:

        ``'atmos.5'``   Half-degree primary atmospheric fields (~83 variables).
        ``'atmos.5b'``  Half-degree secondary fields (~500 variables).
        ``'atmos.25'``  Quarter-degree primary fields (~35 variables).
        ``'wave'``      Global wave products.

    member : int or str, default 0
        Ensemble member.  ``0`` = control run; ``1``–``30`` = perturbation
        members; ``'avg'`` = ensemble mean; ``'spr'`` = spread.

    References
    ----------
    * https://www.nco.ncep.noaa.gov/pmb/products/gens/
    * https://registry.opendata.aws/noaa-gefs/
    """

    MODEL_NAME = "GEFS"
    MODEL_DESCRIPTION = "NOAA Global Ensemble Forecast System"
    MODEL_WEBSITES = {
        "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/gens/",
        "AWS": "https://registry.opendata.aws/noaa-gefs/",
    }

    PARAMS = {
        "product": {
            "default": "atmos.5",
            "valid": ["atmos.5", "atmos.5b", "atmos.25", "wave", "chem.5", "chem.25"],
            "descriptions": {
                "atmos.5": "Half-degree primary atmos fields (~83 variables)",
                "atmos.5b": "Half-degree secondary atmos fields (~500 variables)",
                "atmos.25": "Quarter-degree primary atmos fields (~35 variables)",
                "wave": "Global wave products",
                "chem.5": "Chemistry fields; 0.5°",
                "chem.25": "Chemistry fields; 0.25°",
            },
        },
        "member": {
            "default": 0,
            "valid": list(range(0, 31)) + ["avg", "spr"],
            "aliases": {"control": 0, "mean": "avg", "spread": "spr"},
        },
    }

    def _build_sources(self) -> dict:
        d = self.date
        step = self.step
        product = self.params["product"]
        member = self.params["member"]

        # Format member string
        if isinstance(member, int):
            member_str = "c00" if member == 0 else f"p{member:02d}"
        else:
            member_str = member  # 'avg' or 'spr'

        # Wave products use different member names
        if product == "wave":
            if member_str == "spr":
                member_str = "spread"
            elif member_str == "avg":
                member_str = "mean"
        else:
            if member_str == "spread":
                member_str = "spr"
            elif member_str == "mean":
                member_str = "avg"

        filedir = f"gefs.{d:%Y%m%d/%H}"
        idx = [".idx", ".grib2.idx"]

        if d < datetime(2018, 7, 27):
            filepaths = {
                "atmos.5": f"{filedir}/ge{member_str}.t{d:%H}z.pgrb2af{step:03d}",
                "atmos.5b": f"{filedir}/ge{member_str}.t{d:%H}z.pgrb2bf{step:03d}",
            }
        elif d < datetime(2020, 9, 23):
            filepaths = {
                "atmos.5": f"{filedir}/pgrb2a/ge{member_str}.t{d:%H}z.pgrb2af{step:02d}",
                "atmos.5b": f"{filedir}/pgrb2b/ge{member_str}.t{d:%H}z.pgrb2bf{step:02d}",
            }
        else:
            filepaths = {
                "atmos.5": f"{filedir}/atmos/pgrb2ap5/ge{member_str}.t{d:%H}z.pgrb2a.0p50.f{step:03d}",
                "atmos.5b": f"{filedir}/atmos/pgrb2bp5/ge{member_str}.t{d:%H}z.pgrb2b.0p50.f{step:03d}",
                "atmos.25": f"{filedir}/atmos/pgrb2sp25/ge{member_str}.t{d:%H}z.pgrb2s.0p25.f{step:03d}",
                "wave": f"{filedir}/wave/gridded/gefs.wave.t{d:%H}z.{member_str}.global.0p25.f{step:03d}.grib2",
                "chem.5": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{d:%H}z.a2d_0p25.f{step:03d}.grib2",
                "chem.25": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{d:%H}z.a2d_0p25.f{step:03d}.grib2",
            }

        path = filepaths.get(product, filepaths.get("atmos.5"))
        return {
            "aws": GribSource(f"https://noaa-gefs-pds.s3.amazonaws.com/{path}", idx),
            "nomads": GribSource(
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/{path}", idx
            ),
            "google": GribSource(
                f"https://storage.googleapis.com/gfs-ensemble-forecast-system/{path}",
                idx,
            ),
        }


# ---------------------------------------------------------------------------
# RRFS
# ---------------------------------------------------------------------------


class RRFS(HerbieModel):
    """
    NOAA Rapid Refresh Forecast System (RRFS).

    Next-generation convection-allowing ensemble replacing the RAP, NAM,
    and HREF.  Still under development; URL structure may change.

    Parameters
    ----------
    date : str or datetime
        Model initialization datetime (UTC).
    step : int, default 0
        Forecast lead time in hours (0–60).
    product : {'prslev', 'natlev'}, default 'prslev'
        Level type.  Aliases: ``prs→prslev``, ``nat→natlev``.
    domain : {'conus', 'ak', 'hi', 'pr'}, default 'conus'

    References
    ----------
    * https://registry.opendata.aws/noaa-rrfs/
    """

    MODEL_NAME = "RRFS"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh Forecast System"
    MODEL_WEBSITES = {
        "AWS": "https://registry.opendata.aws/noaa-rrfs/",
    }

    PARAMS = {
        "product": {
            "default": "prslev",
            "valid": ["prslev", "natlev", "testbed", "ififip"],
            "aliases": {
                "prs": "prslev",
                "nat": "natlev",
                "pressure": "prslev",
                "native": "natlev",
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
        step = self.step
        product = self.params["product"]
        domain = self.params["domain"]
        resolution = "2p5km" if domain in ("hi", "pr") else "3km"

        path = (
            f"rrfs_a/rrfs.{d:%Y%m%d/%H}/"
            f"rrfs.t{d:%H}z.{product}.{resolution}.f{step:03d}.{domain}.grib2"
        )
        idx = [".grib2.idx", ".idx"]
        return {
            "aws": GribSource(f"https://noaa-rrfs-pds.s3.amazonaws.com/{path}", idx),
        }

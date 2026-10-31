from datetime import datetime

from herbie.experimental.models import ModelTemplate


class GEFSTemplate(ModelTemplate):
    """Global Ensemble Forecast System (GEFS) Model Template."""

    MODEL_NAME = "GEFS"
    MODEL_DESCRIPTION = "NOAA Global Ensemble Forecast System"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/gens/",
        "aws": "https://registry.opendata.aws/noaa-gefs/",
    }

    PARAMS = {
        "product": {
            "default": "atmos.5",
            "valid": ["atmos.5", "atmos.5b", "atmos.25", "wave", "chem.5", "chem.25"],
            "descriptions": {
                "atmos.5": "Half degree atmos PRIMARY fields (~83 variables)",
                "atmos.5b": "Half degree atmos SECONDARY fields (~500 variables)",
                "atmos.25": "Quarter degree atmos PRIMARY fields (~35 variables)",
                "wave": "Global wave products",
                "chem.5": "Chemistry fields on 0.5 degree grid",
                "chem.25": "Chemistry fields on 0.25 degree grid",
            },
        },
        "member": {
            "default": 0,
            "aliases": {
                "control": 0,
                "mean": "avg",
                "spread": "spr",
            },
            "valid": list(range(0, 31)) + ["avg", "spr"],
        },
        "step": {
            "default": 0,
            "valid": range(0, 385),
        },
    }

    INDEX_SUFFIX = [".idx", ".grib2.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        member = self.params.get("member")
        step = self.params.get("step")

        # Convert member to string format
        if isinstance(member, int):
            member_str = f"p{member:02d}" if member > 0 else "c00"
        else:
            member_str = member  # "avg" or "spr"

        # Adjust member naming for wave products
        if product == "wave":
            if member_str == "spr":
                member_str = "spread"
            elif member_str == "avg":
                member_str = "mean"
        elif product.startswith("atmos"):
            if member_str == "spread":
                member_str = "spr"
            elif member_str == "mean":
                member_str = "avg"

        filedir = f"gefs.{date:%Y%m%d/%H}"

        if date < datetime(2018, 7, 27):
            filepaths = {
                "atmos.5": f"{filedir}/ge{member_str}.t{date:%H}z.pgrb2af{step:03d}",
                "atmos.5b": f"{filedir}/ge{member_str}.t{date:%H}z.pgrb2bf{step:03d}",
            }
        elif date < datetime(2020, 9, 23):
            filepaths = {
                "atmos.5": f"{filedir}/pgrb2a/ge{member_str}.t{date:%H}z.pgrb2af{step:02d}",
                "atmos.5b": f"{filedir}/pgrb2b/ge{member_str}.t{date:%H}z.pgrb2bf{step:02d}",
            }
        else:
            filepaths = {
                "atmos.5": f"{filedir}/atmos/pgrb2ap5/ge{member_str}.t{date:%H}z.pgrb2a.0p50.f{step:03d}",
                "atmos.5b": f"{filedir}/atmos/pgrb2bp5/ge{member_str}.t{date:%H}z.pgrb2b.0p50.f{step:03d}",
                "atmos.25": f"{filedir}/atmos/pgrb2sp25/ge{member_str}.t{date:%H}z.pgrb2s.0p25.f{step:03d}",
                "wave": f"{filedir}/wave/gridded/gefs.wave.t{date:%H}z.{member_str}.global.0p25.f{step:03d}.grib2",
                "chem.5": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{date:%H}z.a2d_0p25.f{step:03d}.grib2",
                "chem.25": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{date:%H}z.a2d_0p25.f{step:03d}.grib2",
            }

        path = filepaths.get(product)

        return {
            "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/{path}",
            "google": f"https://storage.googleapis.com/global-ensemble-forecast-system/{path}",
        }

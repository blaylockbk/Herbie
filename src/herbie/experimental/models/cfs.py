from datetime import datetime

from herbie.experimental.models import ModelTemplate


class CFSTemplate(ModelTemplate):
    """Climate Forecast System (CFS) Model Template."""

    MODEL_NAME = "CFS"
    MODEL_DESCRIPTION = "NOAA Climate Forecast System"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/cfs/",
        "aws": "https://registry.opendata.aws/noaa-cfs/",
        "azure": "https://planetarycomputer.microsoft.com/dataset/storage/noaa-cfs",
        "ncei": "https://www.ncei.noaa.gov/products/weather-climate-models/climate-forecast-system",
    }

    PARAMS = {
        "product": {
            "default": "6_hourly",
            "valid": ["time_series", "6_hourly", "monthly_means"],
            "descriptions": {
                "time_series": "CFS time series products",
                "6_hourly": "CFS 6 hourly products",
                "monthly_means": "CFS monthly products",
            },
        },
        "member": {
            "default": 1,
            "valid": [1, 2, 3, 4],
        },
        "step": {
            "default": 0,
            "valid": range(0, 1, 1),  # Typically daily or 6-hourly data
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        member = self.params.get("member")
        step = self.params.get("step", 0)

        urls = {}

        if product == "time_series":
            # Note: This requires 'variable' parameter to be set
            variable = self.params.get("variable", "tmp2m")
            post_root = f"cfs.{date:%Y%m%d/%H}/time_grib_{member:02d}/{variable}.{member:02d}.{date:%Y%m%d%H}.daily.grb2"
            urls["aws"] = f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}"
            urls["nomads"] = (
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}"
            )

        elif product == "6_hourly":
            kind = self.params.get("kind", "pgbf")
            # Calculate valid date from step
            valid_date = self.valid_date
            post_root = f"cfs.{date:%Y%m%d/%H}/6hrly_grib_{member:02d}/{kind}{valid_date:%Y%m%d%H}.{member:02d}.{date:%Y%m%d%H}.grb2"
            urls["aws"] = f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}"
            urls["nomads"] = (
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}"
            )

        elif product == "monthly_means":
            kind = self.params.get("kind", "pgbf")
            month = self.params.get("month", 1)
            hour = self.params.get("hour")
            # Calculate valid month
            valid_month = datetime(date.year, date.month, 1) + __import__(
                "datetime"
            ).timedelta(days=30 * month - 1)
            if hour is None:
                post_root = f"cfs.{date:%Y%m%d/%H}/monthly_grib_{member:02d}/{kind}.{member:02d}.{date:%Y%m%d%H}.{valid_month:%Y%m}.avrg.grib.grb2"
            else:
                post_root = f"cfs.{date:%Y%m%d/%H}/monthly_grib_{member:02d}/{kind}.{member:02d}.{date:%Y%m%d%H}.{valid_month:%Y%m}.avrg.grib.{hour:02d}Z.grb2"
            urls["aws"] = f"https://noaa-cfs-pds.s3.amazonaws.com/{post_root}"
            urls["nomads"] = (
                f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/cfs/prod/{post_root}"
            )

        return urls

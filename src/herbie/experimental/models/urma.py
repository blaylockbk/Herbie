from herbie.experimental.models import ModelTemplate


class URMATemplate(ModelTemplate):
    """CONUS Un-Restricted Mesoscale Analysis (URMA) Model Template."""

    MODEL_NAME = "URMA"
    MODEL_DESCRIPTION = "NOAA CONUS Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "descriptions": {
                "anl": "Analysis",
                "err": "Analysis Forecast Error",
                "ges": "Forecasts",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 1),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")

        path = (
            f"urma2p5.{date:%Y%m%d}/urma2p5.t{date:%H}z.2dvar{product}_ndfd.grb2_wexp"
        )

        return {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}",
        }


class URMAAKTemplate(ModelTemplate):
    """Alaska Un-Restricted Mesoscale Analysis (URMA) Model Template."""

    MODEL_NAME = "URMA_AK"
    MODEL_DESCRIPTION = "NOAA Alaska Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "descriptions": {
                "anl": "Analysis",
                "err": "Analysis Forecast Error",
                "ges": "Forecasts",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 1),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")

        path = f"akurma.{date:%Y%m%d}/akurma.t{date:%H}z.2dvar{product}_ndfd_3p0.grb2"

        return {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}",
        }


class URMAHITemplate(ModelTemplate):
    """Hawaii Un-Restricted Mesoscale Analysis (URMA) Model Template."""

    MODEL_NAME = "URMA_HI"
    MODEL_DESCRIPTION = "NOAA Hawaii Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "descriptions": {
                "anl": "Analysis",
                "err": "Analysis Forecast Error",
                "ges": "Forecasts",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 1),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")

        path = f"hiwurma.{date:%Y%m%d}/hiwurma.t{date:%H}z.2dvar{product}_ndfd_2p5.grb2"

        return {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}",
        }


class URMAPRTemplate(ModelTemplate):
    """Puerto Rico Un-Restricted Mesoscale Analysis (URMA) Model Template."""

    MODEL_NAME = "URMA_PR"
    MODEL_DESCRIPTION = "NOAA Puerto Rico Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges"],
            "descriptions": {
                "anl": "Analysis",
                "err": "Analysis Forecast Error",
                "ges": "Forecasts",
            },
        },
        "step": {
            "default": 0,
            "valid": range(0, 1),
        },
    }

    INDEX_SUFFIX = [".grb2.idx", ".idx", ".grib.idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")

        path = f"prurma.{date:%Y%m%d}/prurma.t{date:%H}z.2dvar{product}_ndfd.grb2"

        return {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}",
        }

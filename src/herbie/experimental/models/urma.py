from herbie.experimental.models import ModelTemplate


class URMATemplate(ModelTemplate):
    """Un-Restricted Mesoscale Analysis (URMA) Model Template.

    Supports multiple domains:
    - CONUS (urma2p5): Continental United States at 2.5km resolution
    - Alaska (akurma): Alaska at 3.0km resolution
    - Hawaii (hiurma): Hawaii at 2.5km resolution
    - Puerto Rico (prurma): Puerto Rico
    - Precipitation (pcpurma): Precipitation analysis
    """

    MODEL_NAME = "URMA"
    MODEL_DESCRIPTION = "NOAA Un-Restricted Mesoscale Analysis"
    MODEL_WEBSITES = {
        "nomads": "https://www.nco.ncep.noaa.gov/pmb/products/rtma/",
        "aws": "https://registry.opendata.aws/noaa-rtma/",
    }

    PARAMS = {
        "domain": {
            "default": "conus",
            "valid": ["conus", "alaska", "hawaii", "puertorico"],
            "descriptions": {
                "conus": "Continental US (2.5km resolution)",
                "alaska": "Alaska (3.0km resolution)",
                "hawaii": "Hawaii (2.5km resolution)",
                "puertorico": "Puerto Rico",
            },
        },
        "product": {
            "default": "anl",
            "valid": ["anl", "err", "ges", "minRH", "maxRH", "pcp_01h", "pcp_06h"],
            "descriptions": {
                "anl": "2D Variational Analysis",
                "err": "Analysis Forecast Error",
                "ges": "First Guess (Forecast)",
                "minRH": "Minimum Relative Humidity (CONUS only, ~08Z)",
                "maxRH": "Maximum Relative Humidity (CONUS only, ~20Z)",
                "pcp_01h": "1-hour Precipitation (CONUS only)",
                "pcp_06h": "6-hour Precipitation (CONUS only)",
            },
        },
        "pcp_type": {
            "default": "wexp",
            "valid": ["wexp", "mask"],
            "descriptions": {
                "wexp": "With experimental data",
                "mask": "Masked precipitation",
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
        domain = self.params.get("domain")
        product = self.params.get("product")
        pcp_type = self.params.get("pcp_type")

        # Map domain parameter to directory prefix
        domain_prefixes = {
            "conus": "urma2p5",
            "alaska": "akurma",
            "hawaii": "hiurma",
            "puertorico": "prurma",
        }

        prefix = domain_prefixes[domain]

        # Handle different product types
        if product in ["anl", "err", "ges"]:
            # Standard 2D variational analysis products
            if domain == "conus":
                filename = f"{prefix}.t{date:%H}z.2dvar{product}_ndfd.grb2_wexp"
            elif domain == "alaska":
                filename = f"{prefix}.t{date:%H}z.2dvar{product}_ndfd_3p0.grb2"
            elif domain == "hawaii":
                filename = f"{prefix}.t{date:%H}z.2dvar{product}_ndfd_2p5.grb2"
            elif domain == "puertorico":
                filename = f"{prefix}.t{date:%H}z.2dvar{product}_ndfd.grb2"

        elif product == "minRH":
            # Minimum RH - CONUS only, typically at 08Z
            if domain != "conus":
                raise ValueError("minRH product only available for CONUS domain")
            filename = f"{prefix}.t{date:%H}z.minRH_ndfd.grb2_wexp"

        elif product == "maxRH":
            # Maximum RH - CONUS only, typically at 20Z
            if domain != "conus":
                raise ValueError("maxRH product only available for CONUS domain")
            filename = f"{prefix}.t{date:%H}z.maxRH_ndfd.grb2_wexp"

        elif product in ["pcp_01h", "pcp_06h"]:
            # Precipitation products - CONUS only
            if domain != "conus":
                raise ValueError(
                    "Precipitation products only available for CONUS domain"
                )
            filename = f"{prefix}.{date:%Y%m%d%H}.{product}.{pcp_type}.grb2"

        path = f"{prefix}.{date:%Y%m%d}/{filename}"

        return {
            "aws": f"https://noaa-urma-pds.s3.amazonaws.com/{path}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/urma/prod/{path}",
        }

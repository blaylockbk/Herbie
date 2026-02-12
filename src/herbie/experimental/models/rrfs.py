from herbie.experimental.models import ModelTemplate


class RRFSTemplate(ModelTemplate):
    """Rapid Refresh Forecast System (RRFS) Ensemble Model Template."""

    MODEL_NAME = "RRFS"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh Forecast System Ensemble"
    MODEL_WEBSITES = {
        "aws": "https://registry.opendata.aws/noaa-rrfs/",
    }

    PARAMS = {
        "product": {
            "default": "prslev",
            "aliases": {
                "prs": "prslev",
                "nat": "natlev",
                "pressure": "prslev",
                "native": "natlev",
            },
            "valid": ["prslev", "natlev", "testbed", "ififip"],
            "descriptions": {
                "prslev": "Pressure levels",
                "natlev": "Native levels",
                "testbed": "Testbed product",
                "ififip": "IFIFIP product",
            },
        },
        "member": {
            "default": 0,
            "aliases": {
                "control": "control",
            },
            "valid": list(range(0, 35)) + ["control"],
        },
        "domain": {
            "default": "conus",
            "aliases": {
                "conus": "conus",
                "alaska": "ak",
                "hawaii": "hi",
                "puerto rico": "pr",
            },
            "valid": ["conus", "ak", "hi", "pr"],
        },
        "step": {
            "default": 0,
            "valid": range(0, 61),
        },
    }

    INDEX_SUFFIX = [".grib2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        member = self.params.get("member")
        domain = self.params.get("domain")
        step = self.params.get("step")

        # Convert member to string format
        if isinstance(member, int):
            member_str = f"mem{member:04d}"
        else:
            member_str = member  # "control"

        # Build URL parts
        member_path = member_str
        filedir = f"rrfs_a/rrfs_a.{date:%Y%m%d/%H}/{member_path}"

        urls = {}

        # Generate URLs with different format variations
        # Handle different domain formats
        if domain == "conus":
            domain_suffixes = ["conus_3km", "conus"]
        else:
            domain_suffixes = [domain]

        # Handle different member formats for ensemble products
        if member_str.startswith("mem"):
            member_num = int(member_str[3:])
            member_prefixes = [f".m{member_num:02d}", ""]
        else:
            member_prefixes = [""]

        # Generate all possible URL combinations
        url_count = 0
        for member_prefix in member_prefixes:
            for domain_suffix in domain_suffixes:
                url = (
                    f"https://noaa-rrfs-pds.s3.amazonaws.com/{filedir}/"
                    f"rrfs.t{date:%H}z{member_prefix}.{product}.f{step:03d}.{domain_suffix}.grib2"
                )
                # Clean up double dots
                url = url.replace("..", ".")
                urls[f"aws_{url_count}"] = url
                url_count += 1

        return urls


class RRFSOldTemplate(ModelTemplate):
    """Rapid Refresh Forecast System (RRFS) Old Format Model Template."""

    MODEL_NAME = "RRFS_OLD"
    MODEL_DESCRIPTION = "NOAA Rapid Refresh Forecast System Ensemble (Old Format)"
    MODEL_WEBSITES = {
        "aws": "https://registry.opendata.aws/noaa-rrfs/",
    }

    PARAMS = {
        "product": {
            "default": "mean",
            "valid": [
                "mean",
                "avrg",
                "eas",
                "ffri",
                "lpmm",
                "pmmn",
                "prob",
                "testbed.conus",
                "na",
            ],
            "descriptions": {
                "mean": "Ensemble mean",
                "avrg": "Ensemble average products",
                "eas": "Ensemble Agreement Scale",
                "ffri": "Ensemble probability products",
                "lpmm": "Localized probability matched mean",
                "pmmn": "Probability matched mean",
                "prob": "Ensemble probability products",
                "testbed.conus": "Surface grids (one for each member)",
                "na": "Native grids (one for each member)",
            },
        },
        "member": {
            "default": 0,
            "valid": list(range(0, 20)),
        },
        "step": {
            "default": 0,
            "valid": range(0, 61),
        },
    }

    INDEX_SUFFIX = [".grib2.idx", ".idx"]

    def get_remote_urls(self) -> dict[str, str]:
        """Return all the URLs.

        Dict order defines priority.
        """
        date = self.date
        product = self.params.get("product")
        member = self.params.get("member")
        step = self.params.get("step")

        urls = {}

        # Ensemble product URLs
        urls["aws_ensprod"] = (
            f"https://noaa-rrfs-pds.s3.amazonaws.com/rrfs.{date:%Y%m%d/%H}/"
            f"ensprod/rrfsce.t{date:%H}z.conus.{product}.f{step:02d}.grib2"
        )

        # Member product URLs
        urls["aws_member"] = (
            f"https://noaa-rrfs-pds.s3.amazonaws.com/rrfs.{date:%Y%m%d/%H}/"
            f"mem{member:02d}/rrfs.t{date:%H}z.mem{member:02d}.{product}f{step:03d}.grib2"
        )

        return urls

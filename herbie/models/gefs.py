## Added by Brian Blaylock
## March 11, 2022

"""
A Herbie template for the GEFS (2017-Present) and GEFS Reforecast (2000-2019)
GRIB2 products.


"""


class gefs:
    def template(self):
        self.DESCRIPTION = "Global Ensemble Forecast System (GEFS)"
        self.DETAILS = {
            "Amazon Open Data": "https://registry.opendata.aws/noaa-gefs/",
            "NOMADS": "https://www.nco.ncep.noaa.gov/pmb/products/gens/",
        }

        self.PRODUCTS = {
            "atmos.5": "Half degree atmos PRIMARY fields (pgrb2ap5); ~83 most common variables.",
            "atmos.5b": "Half degree atmos SECONDARY fields (pgrb2bp5); ~500 least common variables",
            "atmos.25": "Quarter degree atmos PRIMARY fields (pgrb2sp25); ~35 most common variables",
            "wave": "Global wave products.",
            "chem.5": "Chemistry fields on 0.5 degree grid",
            "chem.25": "Chemistry fields on 0.25 degree grid",
        }

        if self.product is None:
            # Just select the first PRODUCT as default
            self.product = list(self.PRODUCTS)[0]

        if self.product == "wave":
            if self.member == "spr":
                self.member = "spread"
            elif self.member == "avg":
                self.member = "mean"
        elif self.product.startswith("atmos"):
            if self.member == "spread":
                self.member = "spr"
            elif self.member == "mean":
                self.member = "avg"

        if self.member == 0:
            self.member = "c00"
        elif isinstance(self.member, int):
            self.member = f"p{self.member:02d}"

        filedir = f"gefs.{self.date:%Y%m%d/%H}"
        filepaths = {
            "atmos.5": f"{filedir}/atmos/pgrb2ap5/ge{self.member}.t{self.date:%H}z.pgrb2a.0p50.f{self.fxx:03d}",
            "atmos.5b": f"{filedir}/atmos/pgrb2bp5/ge{self.member}.t{self.date:%H}z.pgrb2b.0p50.f{self.fxx:03d}",
            "atmos.25": f"{filedir}/atmos/pgrb2sp25/ge{self.member}.t{self.date:%H}z.pgrb2s.0p25.f{self.fxx:03d}",
            "wave": f"{filedir}/wave/gridded/gefs.wave.t{self.date:%H}z.{self.member}.global.0p25.f{self.fxx:03d}.grib2",
            "chem.5": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{self.date:%H}z.a2d_0p25.f{self.fxx:03d}.grib2",
            "chem.25": f"{filedir}/chem/pgrb2ap25/gefs.chem.t{self.date:%H}z.a2d_0p25.f{self.fxx:03d}.grib2",
        }

        valid_members = {
            "atmos.5": [f"p{i:02d}" for i in range(1, 31)] + ["c00", "spr", "avg"],
            "atmos.5b": [f"p{i:02d}" for i in range(1, 31)],
            "atmos.25": [f"p{i:02d}" for i in range(1, 31)] + ["c00", "spr", "avg"],
            "wave": [f"p{i:02d}" for i in range(1, 31)] + ["spread", "mean", "prob"],
            "chem.5": None,
            "chem.25": None,
        }

        filepath = filepaths.get(self.product)
        if filepath is None:
            raise ValueError(
                f"product={self.product} not recognized. Must be one of {self.PRODUCTS.keys()}"
            )

        _member = valid_members.get(self.product)
        if _member is not None and self.member not in _member:
            raise ValueError(
                f"For GEFS product {self.product}, member must be one of {_member}"
            )

        self.SOURCES = {
            "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/{filepath}",
            "nomads": f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/{filepath}",
            "google": f"https://storage.googleapis.com/gfs-ensemble-forecast-system/{filepath}",
            "azure": f"https://noaagefs.blob.core.windows.net/gefs/{filepath}",
        }

        self.IDX_SUFFIX = [".idx", ".grb2.idx", ".grib2.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gefs_reforecast:
    """Template for GEFS Reforecast data

    These grib files are organized different from other model types.
    The files are grouped into variables and clumped by forecast range.
    Thus, instead of a one file having all the variables for that lead time,
    a file has one variable for many lead times. This changes the way
    a user would use Herbie to access GEFS data. A user will need to supply
    the "variable". For getting specific grib messages, you will use the
    "searchString" argument to key in on the variable of interest. However,
    you will still need to give a value for "fxx" to tell Herbie which
    directory to look for. Yeah, it's a little different paradigm for Herbie,
    but we can work with it.

    Provide arguments for

    - date (2000-2019)
    - member {1,2,3,4}
    - fxx (0-384)
    - variable_level (e.g., tmp_2m, acpc_sfc, ugrd_10m, etc.)
    """

    def template(self):
        self.DESCRIPTION = "Global Ensemble Forecast System (GEFS)"
        self.DETAILS = {
            "aws": "https://registry.opendata.aws/noaa-gefs-reforecast/",
        }
        self.PRODUCTS = {
            "GEFSv12/reforecast": "reforecasts for 2000-2019",
        }

        # Adjust "member" argument
        # - Member 0 is the control member
        # - Members 1-4 are the perturbation members
        if self.member == 0:
            member = f"c{self.member:02d}"
        elif self.member > 0 and self.member < 5:
            member = f"p{self.member:02d}"
        else:
            raise ValueError("GEFS 'member' must be one of {0,1,2,3,4}.")

        # Adjust "fxx" argument (given in hours)
        # This is used to define the directory to enter rather than the filename.
        if self.fxx <= 240:
            fxx = "Days:1-10"
        else:
            fxx = "Days:10-16"

        post_root = f"GEFSv12/reforecast/{self.date:%Y/%Y%m%d%H}/{member}/{fxx}/{self.variable_level}_{self.date:%Y%m%d%H}_{member}.grib2"

        self.SOURCES = {
            "aws": f"https://noaa-gefs-retrospective.s3.amazonaws.com/{post_root}",
        }
        self.IDX_SUFFIX = [".grib2.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"

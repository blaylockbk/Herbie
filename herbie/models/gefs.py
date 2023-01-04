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
            "pgrb2ap5": "?? ~83 Most common variables",
            "pgrb2bp5": "?? ~425 Least common variables",
            "pgrb2sp25": "?",
            "wave": "?? Wave products",
            "chem/pgrb2ap25": "?",
            "chem/pgrb2ap5": "?",
        }


        if self.product == "pgrb2ap5":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/atmos/{self.product}/"
            filename = f"geavg.t{self.date:%H}z.pgrb2a.0p50.f{self.fxx:03d}"
        elif self.product == "pgrb2bp5":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/atmos/{self.product}/"
            filename = f"gec00.t{self.date:%H}z.pgrb2b.0p50.f{self.fxx:03d}"
        elif self.product == "pgrb2sp25":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/atmos/{self.product}/"
            filename = f"geavg.t{self.date:%H}z.pgrb2s.0p50.f{self.fxx:03d}"
        elif self.product == "wave":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/wave/gridded/{self.product}/"
            filename = f"gefs.wave.t{self.date:%H}z.c00.global.0p25.f{self.fxx:03d}.grib2"
        elif self.product == "chem/pgrb2ap25":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/chem/pgrb2ap25/"
            filename = f"gefs.chem.t{self.date:%H}}z.a2d_0p25.f{self.fxx:03d}.grib2"
        elif self.product == "chem/pgrb2ap5":
            fileroot = f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/chem/pgrb2ap5/"
            filename = f"gefs.chem.t{self.date:%H}}z.a3d_0p50.f{self.fxx:03d}.grib2"

        self.SOURCES = {
            "aws": f"{fileroot}}{filename}"
        }


        self.IDX_SUFFIX = [".grb2.idx", ".grib2.idx"]
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
        elif self.member > 5:
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

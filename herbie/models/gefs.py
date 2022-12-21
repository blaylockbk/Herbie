## Added by Brian Blaylock
## March 11, 2022

"""
A Herbie template for the GEFS GRIB2 files (2000-2019).

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
"""

class gefs:
    """Template for GEFS data

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

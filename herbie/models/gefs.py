## Added by Brian Blaylock
## March 11, 2022
## Modified by Bryan Guarente
## Novemer 23, 2022

"""
A Herbie template for the GEFS GRIB2 files (2017-present).

"""


class gefs:
    """Template for GEFS data

    Provide arguments for

    - date (2017-present)
    - member {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30}
    - fxx (0-384)
    - variable_level (e.g., tmp_2m, acpc_sfc, ugrd_10m, etc.)
    """

    def template(self):

        self.DESCRIPTION = "Global Ensemble Forecast System (GEFS)"
        self.DETAILS = {
            "aws": "https://registry.opendata.aws/noaa-gefs-pds/",
        }
        self.PRODUCTS = {
            "pgrb2sp25": "common fields, 0.25 degree resolution",
            "pgrb2bp5": "less common fields, 0.5 degree resolution",
            "pgrb2ap5": "less common fields, 0.5 degree resolution",
        }

        # Adjust "member" argument
        # - Member 'avg' is the average of the members
        # - Member 'c' is the control
        # - Member 'spr' is the spread of the members
        # - Members 1-30 are the perturbation members
        if self.member == 'c' or self.member == 'c00':
            member = f"c00"
        elif self.member == 'avg' or self.member == 'mean':
            member = f"avg"
        elif self.member == 'spr' or self.member == 'spread':
            member = f"spr"
        elif self.member > 0:
            member = f"p{self.member:02d}"
        else:
            raise ValueError("GEFS 'member' must be one of {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30}.")

        # Adjust "fxx" argument (given in hours)
        # This is used to define the directory to enter rather than the filename.
        fxx = f"{self.fxx:03d}"

        if self.product == 'pgrb2bp5':
            post_root = f"gefs.{self.date:%Y%m%d}/{self.date:%H}/atmos/{self.product}/ge{member}.t{self.date:%H}z.pgrb2b.0p50.f{fxx}"
        elif self.product == 'pgrb2ap5':
            post_root = f"gefs.{self.date:%Y%m%d}/{self.date:%H}/atmos/{self.product}/ge{member}.t{self.date:%H}z.pgrb2a.0p50.f{fxx}"
        else:
            post_root = f"gefs.{self.date:%Y%m%d}/{self.date:%H}/atmos/{self.product}/ge{member}.t{self.date:%H}z.pgrb2s.0p25.f{fxx}"

        self.SOURCES = {
            "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/{post_root}",
#	    "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/atmos/{self.product}/ge{member}.t{self.date:%H}z.pgrb2s.0p25.f{self.fxx:03d}",
        }
        self.IDX_SUFFIX = [".idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


class gefs_wave:
    def template(self):
        self.DESCRIPTION = "Global Ensemble Forecast System (GEFS) - Wave Products"
        self.DETAILS = {
	    "aws": "https://registry.opendata.aws/noaa-gefs-pds/"
        }
        self.PRODUCTS = {
            "global.0p25": "Global; 0.25 deg resolution"
        }

        # Adjust "member" argument
        # - Member 'avg' is the average of the members
        # - Member 'c' is the control
        # - Member 'spr' is the spread of the members
        # - Members 1-30 are the perturbation members
        if self.member == 'c' or self.member == 'c00':
            member = f"c00"
        elif self.member == 'avg' or self.member == 'mean':
            member = f"mean"
        elif self.member == 'spr' or self.member == 'spread':
            member = f"spread"
        elif self.member > 0:
            member = f"p{self.member:02d}"
        else:
            raise ValueError("GEFS 'member' must be one of {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30}.")

        # Adjust "fxx" argument (given in hours)
        # This is used to define the directory to enter rather than the filename.
        if self.fxx < 100:
            fxx = "0{self.fxx}"
        else:
            fxx = "{self.fxx}"

        post_root = f"gefs.{self.date:%Y%m%d/%H}/wave/gridded/gefs.wave.t{self.date:%H}z.{member}.{self.product}.f{self.fxx:03d}",

        self.SOURCES = {
#            "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/{post_root}"
            "aws": f"https://noaa-gefs-pds.s3.amazonaws.com/gefs.{self.date:%Y%m%d/%H}/wave/gridded/gefs.wave.t{self.date:%H}z.{member}.{self.product}.f{self.fxx:03d}.grib2"
        }

        self.IDX_SUFFIX = [".grib2.idx"]
        self.LOCALFILE = f"{self.get_remoteFileName}"


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


class gefs_ref:
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

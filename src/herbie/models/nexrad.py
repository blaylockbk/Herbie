## Added by Brian Blaylock
## October 13, 2021

"""
Just playing around with downloading radar data, in case I ever need to
do it. I should put non-model related downloads in a separate folder.
This dosn't work very well because the datetime is not predicatble.
I would need to implement a "nearest_time" search like I do in
`GOES-2-go` to make this feasible.

If you know the exact datetime of a file, Hebie can find and download it
H = Herbie('2021-10-13 00:07:21', product='level2', model='nexrad', station='KMAF')
H.download()

But this isn't the best implementation. Instead of reinventing the wheel,
you might want to use `nexradaws`
👉🏻 https://nexradaws.readthedocs.io/en/latest/index.html
"""


class nexrad:
    def template(self):
        self.DESCRIPTION = "NEXRAD Radar "
        self.DETAILS = {
            "aws": "https://registry.opendata.aws/noaa-nexrad/",
        }
        self.PRODUCTS = {
            "level2": "Archived NEXRAD products",
        }
        self.SOURCES = {
            "aws": f"https://noaa-nexrad-{self.product}.s3.amazonaws.com/{self.date:%Y/%m/%d}/{self.station}/{self.station}{self.date:%Y%m%d_%H%M%S}_V06",
            "aws-old": f"https://noaa-nexrad-{self.product}.s3.amazonaws.com/{self.date:%Y/%m/%d}/{self.station}/{self.station}{self.date:%Y%m%d_%H%M%S}",
        }
        self.EXPECT_IDX_FILE = "none"
        self.LOCALFILE = f"{self.get_remoteFileName}"

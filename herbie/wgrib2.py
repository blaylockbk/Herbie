## Brian Blaylock
## January 27, 2023

"""
==================
Wrapper for wgrib2
==================

The ``wgrib2`` utility has some useful features. However, it can not
be installed on windows (at least, not very easily).

"""

from herbie import Path
from shutil import which
import subprocess


class WGRIB2:
    """Wrapper for wgrib2 program."""

    # PATH of wgrib2 program
    wgrib2 = which("wgrib2")

    def __init__(self, grib2file):
        """Wrapper for wgrib2 on a file"""

        self.filepath = Path(grib2file).expand()

    def inventory(self):
        """Return wgrib2-style inventory of GRIB2 file."""
        p = subprocess.run(
            f"{self.wgrib2} -s {self.filepath}",
            shell=True,
            capture_output=True,
            encoding="utf-8",
            check=True,
        )
        return p.stdout

    def create_inventory_file(self, overwrite=False):
        """Create and save wgrib2 inventory for GRIB2 file/files."""
        files = []
        if self.filepath.is_dir():
            # List all GRIB2 files in the directory
            files = list(self.filepath.rglob("*.grib2*"))
        elif self.filepath.is_file():
            # The path is a single file
            files = [self.filepath]

        if not files:
            raise ValueError(f"No grib2 files were found in {self.filepath}")

        for f in files:
            f_idx = Path(str(f) + ".idx")
            if not f_idx.exists() or overwrite:
                # Create an index using wgrib2's simple inventory option
                # if it doesn't already exist or if overwrite is True.
                index_data = self.inventory(Path(f))
                with open(f_idx, "w+") as out_idx:
                    out_idx.write(index_data)

    def area_subset(self, lon_min, lon_max, lat_min, lat_max, OUTFILE=None):
        """Subset a GRIB2 file by geographical area."""
        raise NotImplementedError(
            "Work in progress: https://github.com/blaylockbk/Herbie/issues/109"
        )

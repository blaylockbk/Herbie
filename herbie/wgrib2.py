## Brian Blaylock
## January 28, 2023

"""
==================
Wrapper for wgrib2
==================

The ``wgrib2`` utility has some useful features. However, it can not
be installed on windows (at least, not very easily).

Usage
-----

.. code:: python

    from herbie.wgrib2 import wgrib2

    # Get path to wgrib2 executable
    print(wgrib2.wgrib2)

    # Get Inventory for a GRIB2 file as string
    wgrib2.inventory("/path/to/file.grib2")

    # Create .idx files for GRIB2 file
    wgrib2.create_inventory_file("/path/to/file.grib2")

"""

from herbie import Path
from shutil import which
import subprocess


def run_command(cmd):
    p = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        encoding="utf-8",
        check=True,
    )
    return p.stdout


class _WGRIB2:
    """Wrapper for wgrib2 program."""

    # PATH to wgrib2 executable
    wgrib2 = which("wgrib2")

    def inventory(self, FILE):
        """Return wgrib2-style inventory of GRIB2 file."""
        cmd = f"{self.wgrib2} -s {Path(FILE).expand()}"
        return run_command(cmd)

    def create_inventory_file(self, FILE, suffix=".grib2", overwrite=False):
        """Create and save wgrib2 inventory files for GRIB2 file/files."""
        FILE = Path(FILE).expand()
        if FILE.is_dir():
            # List all GRIB2 files in the directory
            files = list(FILE.rglob(f"*{suffix}"))
        elif FILE.is_file():
            # The path is a single file
            files = [FILE]

        if not files:
            raise ValueError(f"No grib2 files were found in {FILE}")

        for f in files:
            f_idx = Path(str(f) + ".idx")
            if not f_idx.exists() or overwrite:
                # Create an index using wgrib2's simple inventory option
                # only if it doesn't already exist or if overwrite is True.
                index_data = self.inventory(Path(f))
                with open(f_idx, "w+") as out_idx:
                    out_idx.write(index_data)

    def region(self, FILE, lon_min, lon_max, lat_min, lat_max, *, name=None):
        """Subset a GRIB2 file by geographical region.

        See https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/small_grib.html

        Parameters
        ----------
        FILE : path-like
            Path to the grib2 file you wish to subset into a region.
        lon_min, lon_max, lat_min, lat_max : float
            Longitude and Latitude bounds representing the region of interest.
        name : str
            Name of the region. Output grib will be saved to a new file with
            the ``name`` prepended to the filename.
        """
        FILE = Path(FILE).expand()

        if name is None:
            OUTFILE = FILE
        else:
            OUTFILE = FILE.parent / f"{name}_{FILE.name}"

        cmd = f"{self.wgrib2} {Path(FILE).expand()} --small_grib {lon_min}:{lon_max} {lat_min}:{lat_max} {OUTFILE} -set_grib_type same"

        run_command(cmd)
        print(f"Create region subset file {OUTFILE}")

    def vector_relative(self, FILE):
        """
        Check if vector quantities are "grid relative" or "earth relative"

        See "What are Earth and Grid Relative Winds" on https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/new_grid_intro.html

        Read my thought on the subject
        https://github.com/blaylockbk/pyBKB_v2/blob/master/demos/HRRR_earthRelative_vs_gridRelative_winds.ipynb
        """
        cmd = f"{self.wgrib2} -vector_dir {Path(FILE).expand()}"

        out = run_command(cmd)
        relative = {i.split(":")[-1] for i in out.split()}

        if relative == {"winds(grid)"}:
            print("All winds are grid-relative winds.")
        elif relative == {"winds(earth)"}:
            print("All winds are earth-relative winds.")
        else:
            print("Mixed vector relative winds; pay attention to output.")
        return relative


wgrib2 = _WGRIB2()

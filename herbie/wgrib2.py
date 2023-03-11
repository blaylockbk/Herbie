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

    def create_inventory_file(self, path, suffix=".grib2"):
        """Create and save wgrib2 inventory files for GRIB2 file/files.

        Note that this will overwrite any existing inventory file.

        Parameters
        ----------
        path : pathlib.path
            If path is a file, then make inventory file for that file.
            If path is a directory, then make inventory files for all
            files with the indicated suffix.
        suffix : {".grib2", ".grib", ".grb", etc.}
            If path specified is a directory, then this is the suffix to
            look for GRIB2 files.
        """
        path = Path(path).expand()
        if path.is_dir():
            # List all GRIB2 files in the directory
            files = list(path.rglob(f"*{suffix}"))
        elif path.is_file():
            # The path is a single file
            files = [path]

        if not files:
            raise ValueError(f"No grib2 files were found in {path}")

        idx_files = []
        for f in files:
            f_idx = Path(str(f) + ".idx")
            idx_files.append(f_idx)
            index_data = self.inventory(Path(f))
            with open(f_idx, "w+") as out_idx:
                out_idx.write(index_data)

        if len(idx_files) == 1:
            return idx_files[0]
        else:
            return idx_files

    def region(self, path, extent, *, name="region", suffix=".grib2", create_idx=True):
        """Subset a GRIB2 file by geographical region.

        See https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/small_grib.html

        Parameters
        ----------
        path : path-like
            Path to the grib2 file you wish to subset into a region.
            If path is a file, then make region subset for that file.
            If path is a directory, then make region subset for all
            files with the indicated suffix.
        extent : 4-item tuple or list
            Longitude and Latitude bounds representing the region of interest.
            (lon_min, lon_max, lat_min, lat_max) : float
        name : str
            Name of the region. Output grib will be saved to a new file with
            the ``name`` prepended to the filename.
        suffix : {".grib2", ".grib", ".grb", etc.}
            If path specified is a directory, then this is the suffix to
            look for GRIB2 files.
        create_idx : bool
            If True, then make an inventory file for the GRIB2 region subest.
        """
        path = Path(path).expand()
        if path.is_dir():
            # List all GRIB2 files in the directory
            files = list(path.rglob(f"*{suffix}"))
        elif path.is_file():
            # The path is a single file
            files = [path]

        if not files:
            raise ValueError(f"No grib2 files were found in {path}")

        if len(extent) != 4:
            raise TypeError(
                "Region extent must be (lon_min, lon_max, lat_min, lat_max)"
            )

        lon_min, lon_max, lat_min, lat_max = extent

        OUTFILES = []
        for f in files:
            OUTFILE = path.parent / f"{name}_{path.name}"

            cmd = f"{self.wgrib2} {Path(path).expand()} -small_grib {lon_min}:{lon_max} {lat_min}:{lat_max} {OUTFILE} -set_grib_type same"

            run_command(cmd)

            if name is None:
                OUTFILE.rename(f)
                self.create_inventory_file(f)
                OUTFILES.append(f)
            else:
                self.create_inventory_file(OUTFILE)
                OUTFILES.append(OUTFILE)

        if len(OUTFILES) == 1:
            return OUTFILES[0]
        else:
            return OUTFILES

    def vector_relative(self, path):
        """
        Check if vector quantities are "grid relative" or "earth relative"

        See "What are Earth and Grid Relative Winds" on https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/new_grid_intro.html

        Read my thought on the subject
        https://github.com/blaylockbk/pyBKB_v2/blob/master/demos/HRRR_earthRelative_vs_gridRelative_winds.ipynb

        Parameters
        ----------
        path : path-like
            Path to the grib2 file.
        """
        cmd = f"{self.wgrib2} -vector_dir {Path(path).expand()}"

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

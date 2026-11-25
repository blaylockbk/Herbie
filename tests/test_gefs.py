## Brian Blaylock
## February 9, 2022

"""Tests for downloading GEFS model."""

from herbie import Herbie, config

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


def test_gefs():
    H = Herbie(
        "2023-01-01 06:00",
        model="gefs",
        fxx=12,
        member="mean",
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "GEFS grib2 file not found"
    assert H.idx, "GEFS index file not found"


def test_gefs_reforecast():
    H = Herbie(
        "2017-03-14",
        model="gefs_reforecast",
        fxx=12,
        member=0,
        variable_level="tmp_2m",
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "GEFS grib2 file not found"
    assert H.idx, "GEFS index file not found"


def test_gefs_chem5_uses_half_degree_path():
    """chem.5 must resolve to the 0.5° bucket path, not the 0.25° one."""
    H = Herbie(
        "2023-06-08 00:00",
        model="gefs",
        product="chem.5",
        member="c00",
        fxx=3,
        save_dir=save_dir,
    )
    assert "pgrb2ap5" in H.SOURCES["aws"]
    assert "a3d_0p50" in H.SOURCES["aws"]

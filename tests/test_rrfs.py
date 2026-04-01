"""Tests for RRFS model template URL generation."""

from datetime import datetime, timedelta

import pytest

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day) - timedelta(hours=12)

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


def test_rrfs_natlev_domain_forced_to_na():
    """natlev product should always use domain='na', regardless of user input."""
    H = Herbie(
        today,
        model="rrfs",
        product="natlev",
        fxx=0,
        save_dir=save_dir,
    )
    assert H.domain == "na"


def test_rrfs_natlev_overrides_user_domain():
    """Even if user passes domain='conus', natlev should force domain='na'."""
    H = Herbie(
        today,
        model="rrfs",
        product="natlev",
        domain="conus",
        fxx=0,
        save_dir=save_dir,
    )
    assert H.domain == "na"


def test_rrfs_nat_shorthand():
    """The 'nat' shorthand should normalize to 'natlev' and use domain='na'."""
    H = Herbie(
        today,
        model="rrfs",
        product="nat",
        fxx=0,
        save_dir=save_dir,
    )
    assert H.product == "natlev"
    assert H.domain == "na"


def test_rrfs_prslev_defaults_to_conus():
    """prslev product should default domain to 'conus'."""
    H = Herbie(
        today,
        model="rrfs",
        product="prslev",
        fxx=0,
        save_dir=save_dir,
    )
    assert H.domain == "conus"


@pytest.mark.parametrize(
    "domain_in,domain_out",
    [
        ("alaska", "ak"),
        ("hawaii", "hi"),
        ("puerto rico", "pr"),
        ("na", "na"),
        ("conus", "conus"),
    ],
)
def test_rrfs_domain_mapping(domain_in, domain_out):
    """Domain long names should be mapped to their abbreviations."""
    H = Herbie(
        today,
        model="rrfs",
        product="prslev",
        domain=domain_in,
        fxx=0,
        save_dir=save_dir,
    )
    assert H.domain == domain_out


def test_rrfs_natlev_file_exists():
    """Verify the natlev URL actually resolves to a file on S3."""
    H = Herbie(
        today,
        model="rrfs",
        product="natlev",
        fxx=0,
        save_dir=save_dir,
        overwrite=True,
    )
    assert H.grib, "RRFS natlev grib2 file not found"
    assert H.idx, "RRFS natlev index file not found"

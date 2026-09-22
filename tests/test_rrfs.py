"""Tests for RRFS model template URL generation."""

from datetime import datetime, timedelta

import pytest

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day) - timedelta(hours=12)

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


def test_rrfs():
    H = Herbie(
        today,
        model="rrfs",
        fxx=12,
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "RRFS grib2 file not found"
    assert H.idx, "RRFS index file not found"


def test_rrfs_ens():
    H = Herbie(
        today,
        model="rrfs",
        product='2dfldnomads',
        fxx=12,
        member=1,
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "RRFS (ensemble) grib2 file not found"
    assert H.idx, "RRFS (ensemble) index file not found"


def test_rrfs_subh():
    H = Herbie(
        today,
        model="rrfs",
        product='subh',
        fxx=12,
        save_dir=save_dir,
        overwrite=True,
    )

    assert H.grib, "RRFS (subh) grib2 file not found"
    assert H.idx, "RRFS (subh) index file not found"


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


def test_rrfs_2dfld_product_accepted():
    """2dfld should be a valid product and default to domain='conus'."""
    H = Herbie(
        today,
        model="rrfs",
        product="2dfld",
        fxx=0,
        save_dir=save_dir,
    )
    assert H.product == "2dfld"
    assert H.domain == "conus"
    assert "2dfld" in H.SOURCES["aws"]

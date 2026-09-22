"""Tests for RRFS model template URL generation."""

from datetime import datetime, timedelta

import pytest

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day) - timedelta(hours=12)

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"



def test_refs_ffri_defaults_to_conus():
    """ffri product should default domain to 'conus'."""
    H = Herbie(
        today,
        model="refs",
        product="ffri",
        fxx=1,
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
def test_refs_domain_mapping(domain_in, domain_out):
    """Domain long names should be mapped to their abbreviations."""
    H = Herbie(
        today,
        model="refs",
        product="mean",
        domain=domain_in,
        fxx=1,
        save_dir=save_dir,
    )
    assert H.domain == domain_out


def test_refs_fxx_0():
    """fxx=1 should return warning and change fxx to 1."""
    with pytest.warns(UserWarning, match="REFS does not") as warn:
        H = Herbie(
            today,
            model="refs",
            product="mean",
            fxx=0,
            save_dir=save_dir,
        )
        assert H.fxx == 1


def test_refs_ffri_maps_to_conus():
    """if pfduct is ffri, domain should be set to conus."""
    H = Herbie(
        today,
        model="refs",
        product="ffri",
        fxx=1,
        save_dir=save_dir,
    )
    assert H.domain == "conus"


def test_refs_sprd_product_accepted():
    """sprd should be a valid product and default to domain='conus'."""
    H = Herbie(
        today,
        model="refs",
        product="sprd",
        fxx=1,
        save_dir=save_dir,
    )
    assert H.product == "sprd"
    assert H.domain == "conus"
    assert "sprd" in H.SOURCES["aws"]

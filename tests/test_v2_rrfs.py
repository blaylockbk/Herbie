"""Tests for RRFS URL generation in the v2 API."""

from datetime import datetime

from herbie.v2.models.rrfs import RRFS


def test_rrfs_deterministic_sources_use_operational_urls():
    model = RRFS(datetime(2026, 9, 1, 0), step=12)

    expected_path = (
        "rrfs.20260901/00/rrfs.t00z.prslev.3km.f012.conus.grib2"
    )
    assert model.SOURCES["aws"].url == (
        f"https://noaa-rrfs-ops-pds.s3.amazonaws.com/{expected_path}"
    )
    assert model.SOURCES["nomads"].url == (
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/v1.0/"
        f"{expected_path}"
    )


def test_rrfs_subhourly_and_domain_aliases():
    model = RRFS(
        datetime(2026, 9, 1, 6),
        step=3,
        product="subh",
        domain="puerto rico",
    )

    assert model.params["domain"] == "pr"
    assert model.SOURCES["aws"].url.endswith(
        "rrfs.20260901/06/rrfs.t06z.2dfld.2p5km.subh.f003.pr.grib2"
    )


def test_rrfs_ensemble_member_sources():
    model = RRFS(
        datetime(2026, 9, 1, 12),
        step=6,
        product="2dfldnomads",
        member=1,
        domain="alaska",
    )

    expected_path = (
        "rrfsens.20260901/12/m001/"
        "rrfs.t12z.m001.2dfldnomads.3km.f006.ak.grib2"
    )
    assert model.SOURCES["aws"].url == (
        f"https://noaa-rrfs-ops-pds.s3.amazonaws.com/{expected_path}"
    )
    assert model.SOURCES["nomads"].url == (
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/rrfs/v1.0/"
        f"{expected_path}"
    )


def test_rrfs_north_america_resolution():
    model = RRFS(datetime(2026, 9, 1), domain="na")

    assert model.SOURCES["aws"].url.endswith(
        "rrfs.20260901/00/rrfs.t00z.prslev.13km.f000.na.grib2"
    )

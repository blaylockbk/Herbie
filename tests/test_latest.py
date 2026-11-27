"""Tests HerbieWait."""

from herbie import HerbieWait
import pandas as pd
import pytest


def test_HerbieWait():
    run = pd.Timestamp("now", tz="utc").replace(tzinfo=None).floor("1h")
    with pytest.raises(TimeoutError):
        H = HerbieWait(run, model="nam", wait_for="5s", check_interval="1s", fxx=0)


class FakeHerbie:
    """Stand-in for Herbie: the GRIB appears on the 2nd check, its index on the 4th."""

    calls = 0

    def __init__(self, *args, **kwargs):
        FakeHerbie.calls += 1
        self.grib_source = "aws"
        self.grib = "s3://grib" if FakeHerbie.calls >= 2 else None
        self.idx = "s3://grib.idx" if FakeHerbie.calls >= 4 else None


@pytest.fixture
def fake_herbie(monkeypatch):
    """Replace Herbie in herbie.latest by FakeHerbie, without sleeping."""
    import herbie.latest

    FakeHerbie.calls = 0
    monkeypatch.setattr(herbie.latest, "Herbie", FakeHerbie)
    monkeypatch.setattr(herbie.latest.time, "sleep", lambda seconds: None)
    return FakeHerbie


def test_HerbieWait_returns_once_the_grib_exists(fake_herbie):
    """By default, HerbieWait returns as soon as the GRIB file exists."""
    H = HerbieWait("2026-01-01", model="gfs", wait_for="1h", check_interval="1s")
    assert H.grib is not None
    assert H.idx is None  # the default does not wait for the index


def test_HerbieWait_can_wait_for_the_index_file(fake_herbie):
    """With wait_for_index=True, HerbieWait also waits for the index (#569)."""
    H = HerbieWait(
        "2026-01-01",
        model="gfs",
        wait_for="1h",
        check_interval="1s",
        wait_for_index=True,
    )
    assert H.grib is not None
    assert H.idx is not None


def test_HerbieWait_does_not_wait_for_an_index_of_a_local_file(monkeypatch):
    """A local GRIB file is indexed on the fly, so no remote index is awaited."""
    import herbie.latest

    class LocalHerbie:
        def __init__(self, *args, **kwargs):
            self.grib_source = "local"
            self.grib = "/data/file.grib2"
            self.idx = None  # built from the file when needed

    monkeypatch.setattr(herbie.latest, "Herbie", LocalHerbie)
    monkeypatch.setattr(herbie.latest.time, "sleep", lambda seconds: None)
    H = HerbieWait("2026-01-01", model="gfs", wait_for="1h", wait_for_index=True)
    assert H.grib == "/data/file.grib2"


def test_HerbieWait_returns_the_object_it_checked(fake_herbie):
    """HerbieWait returns the object it checked, without another lookup."""
    HerbieWait(
        "2026-01-01",
        model="gfs",
        wait_for="1h",
        check_interval="1s",
        wait_for_index=True,
    )
    assert fake_herbie.calls == 4  # no extra lookup after the index was found

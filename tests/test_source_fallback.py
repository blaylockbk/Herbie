"""Tests that one unreachable source does not abandon the whole search.

Herbie lists several archives for most models precisely so that the others can
answer when one cannot. These tests pin that behaviour: an exception raised while
checking a single source has to skip that source, not the search (see #246).

No network is used. Every remote check is replaced, so the failure modes that
motivated this -- a TLS error behind a corporate proxy, a DNS failure, a rejected
Azure SAS request -- can be reproduced deterministically.
"""

import json

import pytest
import requests

from herbie import Herbie, core

DATE = "2023-01-01"
MODEL = "hrrr"


def _herbie(monkeypatch, *, grib_check, idx_check=None, priority=None):
    """Build a Herbie with every remote check replaced."""
    monkeypatch.setattr(core.Herbie, "_check_grib", grib_check)
    monkeypatch.setattr(
        core.Herbie,
        "_check_idx",
        idx_check
        if idx_check is not None
        else lambda self, url, verbose=False: (
            False,
            None,
        ),
    )
    # Never let a real local file short-circuit the search.
    monkeypatch.setattr(core.Herbie, "get_localFilePath", lambda self, **kw: Nowhere())
    return Herbie(
        DATE,
        model=MODEL,
        product="sfc",
        fxx=0,
        priority=priority or ["aws", "nomads", "google", "azure"],
    )


class Nowhere:
    """A path that does not exist, whatever is asked of it."""

    def exists(self):
        return False

    @property
    def suffix(self):
        return ".grib2"

    def with_suffix(self, suffix):
        return self


# --------------------------------------------------------------------------- #
# find_grib
# --------------------------------------------------------------------------- #
def test_a_failing_source_falls_through_to_the_next(monkeypatch):
    """The reported case: AWS raises an SSLError, so Google should serve it."""
    tried = []

    def check(self, url, min_content_length=10):
        tried.append(url)
        if "amazonaws" in url:
            raise requests.exceptions.SSLError("self-signed certificate in chain")
        return "storage.googleapis" in url

    H = _herbie(monkeypatch, grib_check=check)

    assert H.grib_source == "google"
    assert any("amazonaws" in url for url in tried), "AWS was never attempted"


def test_every_source_failing_reports_nothing_found(monkeypatch):
    """An exhausted search returns empty rather than raising."""

    def check(self, url, min_content_length=10):
        raise requests.exceptions.ConnectionError("network is unreachable")

    H = _herbie(monkeypatch, grib_check=check)

    assert H.grib is None
    assert H.grib_source is None


def test_a_skipped_source_is_logged(monkeypatch, caplog):
    """A silently skipped source would be impossible to diagnose."""

    def check(self, url, min_content_length=10):
        if "amazonaws" in url:
            raise requests.exceptions.ConnectionError("nope")
        return True

    with caplog.at_level("WARNING", logger="herbie.core"):
        _herbie(monkeypatch, grib_check=check)

    assert any("aws" in record.message for record in caplog.records)


def test_a_keyboard_interrupt_still_stops_the_search(monkeypatch):
    """Skipping failures must not swallow a deliberate interruption."""

    def check(self, url, min_content_length=10):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        _herbie(monkeypatch, grib_check=check)


# --------------------------------------------------------------------------- #
# Azure SAS signing
# --------------------------------------------------------------------------- #
class _Response:
    """Minimal stand-in for a requests response."""

    def __init__(self, payload, *, status=200, text=None):
        self._payload = payload
        self.status_code = status
        self._text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"{self.status_code}")

    def json(self):
        if self._text is not None:
            raise json.JSONDecodeError("not json", self._text, 0)
        return self._payload


def test_a_signed_azure_url_is_returned(monkeypatch):
    signed = "https://ai4edataeuwest.blob.core.windows.net/x?sig=abc"
    monkeypatch.setattr(
        requests, "get", lambda url, timeout=None: _Response({"href": signed})
    )

    H = Herbie.__new__(Herbie)

    assert H._sign_azure_url("https://example.blob.core.windows.net/x") == signed


def test_the_signing_endpoint_is_given_a_timeout(monkeypatch):
    """Without one, a stalled token service hangs the search indefinitely."""
    seen = {}

    def fake_get(url, timeout=None):
        seen["timeout"] = timeout
        return _Response({"href": "https://signed"})

    monkeypatch.setattr(requests, "get", fake_get)
    Herbie.__new__(Herbie)._sign_azure_url("https://x.blob.core.windows.net/y")

    assert seen["timeout"] is not None


@pytest.mark.parametrize(
    "response",
    [
        _Response({"msg": "rate limited"}),  # 200, but no 'href'
        _Response({}),  # empty payload
        _Response(None, text="<html>Blocked</html>"),  # a proxy's error page
    ],
    ids=["no-href", "empty", "not-json"],
)
def test_an_unusable_signing_reply_raises_valueerror(monkeypatch, response):
    monkeypatch.setattr(requests, "get", lambda url, timeout=None: response)

    with pytest.raises(ValueError):
        Herbie.__new__(Herbie)._sign_azure_url("https://x.blob.core.windows.net/y")


def test_a_rejected_azure_sign_skips_only_azure(monkeypatch):
    """The original crash: a bad SAS reply aborted the remaining sources.

    Azure is listed last here, so the KeyError it used to raise came *after* the
    sources that could serve the file. Placed first, as it is in several model
    templates, it took the whole search down with it.
    """
    monkeypatch.setattr(
        requests, "get", lambda url, timeout=None: _Response({"msg": "denied"})
    )

    def check(self, url, min_content_length=10):
        return "storage.googleapis" in url

    H = _herbie(monkeypatch, grib_check=check, priority=["azure", "google"])

    assert H.grib_source == "google"


# --------------------------------------------------------------------------- #
# find_idx
# --------------------------------------------------------------------------- #
def test_a_failing_index_source_falls_through(monkeypatch):
    tried = []

    def idx_check(self, url, verbose=False):
        tried.append(url)
        if "amazonaws" in url:
            raise requests.exceptions.SSLError("bad certificate")
        return (True, url + ".idx")

    H = _herbie(
        monkeypatch,
        grib_check=lambda self, url, min_content_length=10: False,
        idx_check=idx_check,
    )

    # Not named outright: a model template drops sources it cannot serve for a
    # given date -- NOMADS keeps only the last few days -- so the source after
    # AWS depends on the date. What matters is that AWS was tried, skipped, and
    # the next surviving source answered.
    assert any("amazonaws" in url for url in tried), "AWS was never attempted"
    remaining = [source for source in H.SOURCES if source != "aws"]
    assert H.idx_source == remaining[0]


def test_finding_an_index_does_not_sign_the_grib_url(monkeypatch):
    """find_idx used to sign the GRIB URL and then never use it.

    _check_idx signs the URL it actually requests, having appended the index
    suffix first, so the call in find_idx produced a token for the GRIB file
    that was discarded -- while still being able to abort the whole search.
    """
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        return _Response({"href": "https://signed"})

    def idx_check(self, url, verbose=False):
        return (True, url + ".idx")

    H = _herbie(
        monkeypatch,
        grib_check=lambda self, url, min_content_length=10: False,
        idx_check=idx_check,
        priority=["azure"],
    )

    # Installed after construction, so only find_idx's own calls are counted:
    # find_grib signs the Azure URL legitimately, because it is the URL it goes
    # on to check.
    monkeypatch.setattr(requests, "get", fake_get)
    H.find_idx()

    assert calls == [], "find_idx signed a URL it does not use"

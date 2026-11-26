"""Tests for HAFS model template and storm lookup."""

from unittest.mock import Mock, patch

import pytest

from herbie import Herbie
from herbie.models.hafs import Storms


@pytest.mark.parametrize("model", ["hafsa", "hafsb"])
@pytest.mark.parametrize("storm", ["93w", "93W"])
def test_hafs_unlisted_storm_id_does_not_crash(tmp_path, model, storm):
    """Storm IDs absent from inphfsa/inphfsb should still build a valid template."""
    fake_storms = Storms()
    fake_storms.__dict__["id_to_name"] = {"29w": "champi"}
    fake_storms.__dict__["name_to_id"] = {"champi": "29w"}

    with patch("herbie.models.hafs.S", fake_storms):
        H = Herbie(
            "2025-09-30T00:00",
            model=model,
            product="storm.atm",
            storm=storm,
            fxx=0,
            save_dir=tmp_path,
            verbose=False,
        )

    flavor = "a" if model == "hafsa" else "b"
    assert H.storm == "93w"
    assert H.storm_name is None
    assert H.PRODUCTS["storm.atm"] == "93W"
    assert (
        H.SOURCES["nomads"]
        == f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/hfs{flavor}.20250930/00/93w.2025093000.hfs{flavor}.storm.atm.f000.grb2"
    )


@pytest.mark.parametrize("model", ["hafsa", "hafsb"])
def test_hafs_known_storm_name_and_id(tmp_path, model):
    """Known storm names and IDs should resolve to ID and formatted product labels."""
    fake_storms = Storms()
    fake_storms.__dict__["id_to_name"] = {"96c": "invest", "29w": "champi"}
    fake_storms.__dict__["name_to_id"] = {"invest": "96c", "champi": "29w"}

    with patch("herbie.models.hafs.S", fake_storms):
        H_by_name = Herbie(
            "2025-09-30T00:00",
            model=model,
            product="storm.atm",
            storm="Champi",
            fxx=6,
            save_dir=tmp_path,
            verbose=False,
        )
        H_by_id = Herbie(
            "2025-09-30T00:00",
            model=model,
            product="storm.atm",
            storm="96c",
            fxx=6,
            save_dir=tmp_path,
            verbose=False,
        )

    assert H_by_name.storm == "29w"
    assert H_by_name.storm_name == "champi"
    assert H_by_name.PRODUCTS["storm.atm"] == "29W-Champi"

    assert H_by_id.storm == "96c"
    assert H_by_id.storm_name == "invest"
    assert H_by_id.PRODUCTS["storm.atm"] == "96C-Invest"


def test_hafs_unknown_storm_name_raises(tmp_path):
    """Unknown alphabetical storm names should still raise ValueError."""
    fake_storms = Storms()
    fake_storms.__dict__["id_to_name"] = {"29w": "champi"}
    fake_storms.__dict__["name_to_id"] = {"champi": "29w"}

    with (
        patch("herbie.models.hafs.S", fake_storms),
        pytest.raises(ValueError, match="storm"),
    ):
        Herbie(
            "2025-09-30T00:00",
            model="hafsa",
            product="storm.atm",
            storm="notastorm",
            fxx=0,
            save_dir=tmp_path,
            verbose=False,
        )


def test_hafs_missing_storm_raises(tmp_path):
    """Missing storm argument should raise ValueError."""
    with pytest.raises(ValueError, match="storm"):
        Herbie(
            "2025-09-30T00:00",
            model="hafsa",
            product="storm.atm",
            fxx=0,
            save_dir=tmp_path,
            verbose=False,
        )


def test_storms_reads_inphfsa_and_inphfsb():
    """Storms.id_to_name should aggregate storms from both inphfsa and inphfsb."""
    responses = {
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/": Mock(
            ok=True,
            text='<a href="message1">message1</a><a href="message2">message2</a>',
        ),
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/message1": Mock(
            ok=True,
            text="JTWC 98S INVEST 261126 0000\n",
        ),
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsa/message2": Mock(
            ok=True,
            text="",
        ),
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsb/": Mock(
            ok=True,
            text='<a href="message1">message1</a>',
        ),
        "https://nomads.ncep.noaa.gov/pub/data/nccf/com/hafs/prod/inphfsb/message1": Mock(
            ok=True,
            text="NHC 96C INVEST 261125 0000\n",
        ),
    }

    with patch(
        "herbie.models.hafs.requests.get", side_effect=lambda url: responses[url]
    ):
        storms = Storms().id_to_name

    assert storms == {"98s": "invest", "96c": "invest"}

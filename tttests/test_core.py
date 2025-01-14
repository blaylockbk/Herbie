"""Tests for Herbie's core functionality."""

from herbie import Herbie


def test_Herbie_bool():
    """Test that Herbie __bool__ dunder method."""
    H = Herbie("2023-01-01", model="hrrr", priority=["aws"])
    assert bool(H)

    H = Herbie("2000-01-01", model="hrrr", priority=["aws"])
    assert not bool(H)

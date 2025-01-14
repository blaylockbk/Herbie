"""Tests HerbieWait."""

from herbie import HerbieWait
import pandas as pd
import pytest


def test_HerbieWait():
    run = pd.Timestamp("now", tz="utc").replace(tzinfo=None).floor("1h")
    with pytest.raises(TimeoutError):
        H = HerbieWait(run, model="nam", wait_for="5s", check_interval="1s", fxx=0)

"""Tests HerbieWait."""

from herbie import HerbieWait
import pandas as pd
import pytest


def test_HerbieWait():
    run = pd.Timestamp("now", tz="utc").replace(tzinfo=None).ceil("1h")
    with pytest.raises(TimeoutError):
        H = HerbieWait(run, model="hrrr", wait_for="5s", check_interval="1s", fxx=0)

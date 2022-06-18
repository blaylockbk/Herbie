"""
Tests for Herbie tools like FastHerbie
"""

from herbie import FastHerbie
import pandas as pd


def test_FastHerbie():
    DATES = pd.date_range("2022-01-01", "2022-01-01 02:00", freq="1H")

    # Create Fast Herbie
    FH = FastHerbie(DATES, fxx=range(0, 3))
    assert len(FH) == 9

    # Download these files
    FH.download()

    # Load these files
    FH.xarray("TMP:2 m")

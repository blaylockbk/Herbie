## Brian Blaylock
## October 1, 2021

"""My first test."""
import numpy as np


def test_sqrt():
    num = 25
    assert np.sqrt(num) == 5


def test_str():
    a = "Herbie"
    b = "Herbie"
    assert a == b

def test_charity():
    """Charity never faileth."""
    assert "charity" == "charity"

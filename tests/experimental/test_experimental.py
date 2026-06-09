import pytest
from herbie.experimental import Herbie


model_arguments = [
    ("gfs", dict(resolution=1.0, product="uncommon"), "TMP"),
    ("hrrr", dict(product="surface"), "TMP"),
    ("hrrr", dict(product="pressure"), "TMP"),
    ("ifs", dict(), "t"),
    ("rtma", dict(), "TMP"),
]


@pytest.mark.parametrize("model,kwargs,searchString", model_arguments)
def test_the_basics(model, kwargs, searchString):
    """Test basic Herbie functionality for various models."""
    H = Herbie("2025-12-10", model=model, **kwargs)
    assert H

    inventory = H.inventory()
    assert len(inventory) > 0

    inventory = H.inventory(searchString)
    assert len(inventory) > 0

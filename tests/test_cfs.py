## Brian Blaylock
## February 9, 2022

"""Tests discovery of CFS model data."""

from herbie import Herbie, config
import pytest
from itertools import product

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


@pytest.mark.parametrize("variable, member", product(["tmp2m", "wnd10m"], [1, 2, 3, 4]))
def test_cfs_timeseries(variable, member):
    H = Herbie(
        "2025-01-01",
        model="cfs",
        product="time_series",
        member=member,
        variable=variable,
    )

    assert H.grib, "CFS grib2 file not found"
    assert H.idx, "CFS index file not found"
    assert len(H.inventory()), "CFS inventory has zero length."


@pytest.mark.parametrize(
    "kind, member", product(["flxf", "pgbf", "ocnf", "ipvf"], [1, 4])
)
def test_cfs_6hour(kind, member):
    H = Herbie(
        "2024-12-25", model="cfs", product="6_hourly", kind=kind, member=member, fxx=12
    )

    assert H.grib, "CFS grib2 file not found"
    assert H.idx, "CFS index file not found"
    assert len(H.inventory()), "CFS inventory has zero length."


@pytest.mark.parametrize(
    "kind, member, hour",
    product(["flxf", "pgbf", "ocnh", "ocnf", "ipvf"], [1, 4], [0, None]),
)
def test_cfs_monthly(kind, member, hour):
    H = Herbie(
        "2024-05-25",
        model="cfs",
        product="monthly_means",
        kind=kind,
        member=member,
        month=1,
        hour=hour,
    )

    assert H.grib, "CFS grib2 file not found"
    assert H.idx, "CFS index file not found"
    assert len(H.inventory()), "CFS inventory has zero length."

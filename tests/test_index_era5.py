# MIT License
# (c) 2023 Andreas Motl <andreas.motl@panodata.org>
# https://github.com/earthobservations
import datetime
from unittest import mock

import numpy as np
import pytest
import xarray as xr
from xarray.testing import assert_equal

from herbie.index.core import NwpIndex
from herbie.index.loader import open_era5_zarr

TEMP2M = "air_temperature_at_2_metres"

TIMERANGE = np.arange(
    start=np.datetime64("1987-10-01 08:00"),
    stop=np.datetime64("1987-10-01 10:59"),
    step=datetime.timedelta(hours=1),
)


@pytest.fixture
def era5_temp2m():
    """
    Provide an instance of `NwpIndex` to the test cases.
    """
    nwp = NwpIndex(name=TEMP2M)
    if not nwp.exists():
        nwp.save(dataset=open_era5_zarr(TEMP2M, 1987, 10, TIMERANGE[0], TIMERANGE[-1]))
    nwp.load()
    return nwp


def test_query_era5_monterey_fahrenheit_point_time(era5_temp2m):
    """
    Query indexed ERA5 NWP data for a specific geopoint and time.
    """

    # Temperatures in Monterey, in Fahrenheit.
    item = (
        era5_temp2m.query(time="1987-10-01 08:00", lat=36.6083, lon=-121.8674)
        .kelvin_to_fahrenheit()
        .data
    )

    # Verify values.
    assert item.values == np.array(73.805008, dtype=np.float32)

    # Verify coordinate.
    assert dict(item.coords) == dict(
        time=xr.DataArray(data=np.datetime64("1987-10-01 08:00"), name="time"),
        lat=xr.DataArray(data=np.float32(36.5), name="lat"),
        lon=xr.DataArray(data=np.float32(-121.75), name="lon"),
    )


def test_query_era5_berlin_celsius_point_timerange(era5_temp2m):
    """
    Query indexed ERA5 NWP data for the whole time range at a specific geopoint.
    """

    # Temperatures in Berlin, in Celsius.
    result = era5_temp2m.query(lat=52.51074, lon=13.43506).kelvin_to_celsius().data
    assert len(result.data) == 3
    assert result.shape == (3,)

    # Verify values and coordinates.
    reference = xr.DataArray(
        data=np.array([6.600006, 6.600006, 6.600006], dtype=np.float32),
        coords=dict(
            time=xr.DataArray(data=TIMERANGE),
            lat=xr.DataArray(data=np.float32(52.5)),
            lon=xr.DataArray(data=np.float32(13.5)),
        ),
    )
    reference = reference.swap_dims(dim_0="time")
    assert_equal(result, reference)


def test_query_era5_bbox_time(era5_temp2m):
    """
    Query indexed ERA5 NWP data for a given area, defined by a bounding box.

    http://bboxfinder.com/
    """

    # Temperatures in Monterey area, in Fahrenheit.
    result = (
        era5_temp2m.query(
            time="1987-10-01 08:00",
            lat=(36.450837, 36.700907),
            lon=(-122.166252, -121.655045),
        )
        .kelvin_to_fahrenheit()
        .data
    )
    assert len(result.data) == 2
    assert result.shape == (2, 3)

    # Verify values and coordinates.
    reference = xr.DataArray(
        data=np.array(
            [[73.58001, 71.89251, 70.88001], [74.93001, 75.717514, 73.80501]],
            dtype=np.float32,
        ),
        dims=("lat", "lon"),
        coords=dict(
            time=xr.DataArray(data=np.datetime64("1987-10-01 08:00")),
            lat=xr.DataArray(
                data=np.array([36.75, 36.5], dtype=np.float32), dims=("lat",)
            ),
            lon=xr.DataArray(
                data=np.array([-122.25, -122.0, -121.75], dtype=np.float32),
                dims=("lon",),
            ),
        ),
    )
    assert_equal(result, reference)


def test_query_era5_geoslice_time(era5_temp2m):
    """
    Query indexed ERA5 NWP data for a given slice on the latitude coordinate,
    along the same longitude coordinates.
    """

    # Temperatures for whole slice.
    result = (
        era5_temp2m.query(
            time="1987-10-01 08:00", lat=None, lon=(-122.166252, -121.655045)
        )
        .kelvin_to_celsius()
        .data
    )
    assert len(result.data) == 721
    assert result.shape == (721, 3)

    # Verify coordinates.
    reference = xr.DataArray(
        data=mock.ANY,
        dims=("lat", "lon"),
        coords=dict(
            time=xr.DataArray(data=np.datetime64("1987-10-01 08:00")),
            lat=xr.DataArray(
                data=np.arange(start=90.0, stop=-90.01, step=-0.25, dtype=np.float32),
                dims=("lat",),
            ),
            lon=xr.DataArray(
                data=np.array([-122.25, -122.0, -121.75], dtype=np.float32),
                dims=("lon",),
            ),
        ),
    )
    assert_equal(result, reference)

    # Verify values of first and last record, and its coordinate.
    assert result[0].values.tolist() == [
        -21.587493896484375,
        -21.587493896484375,
        -21.587493896484375,
    ]
    assert result[0].coords["lat"] == 90

    assert result[-1].values.tolist() == [
        -43.837493896484375,
        -43.837493896484375,
        -43.837493896484375,
    ]
    assert result[-1].coords["lat"] == -90.0


def test_query_era5_point_timerange_tuple(era5_temp2m):
    """
    Query indexed ERA5 NWP data within given time range.
    This variant uses a `tuple` for defining time range boundaries.

    While the input dataset contains three records, filtering by
    time range should only yield two records.
    """

    # Temperatures for whole slice.
    result = (
        era5_temp2m.query(
            time=(np.datetime64("1987-10-01 08:00"), np.datetime64("1987-10-01 09:05")),
            lat=52.51074,
            lon=13.43506,
        )
        .kelvin_to_celsius()
        .data
    )
    assert len(result.data) == 2
    assert result.shape == (2,)

    # Verify values and coordinates.
    timerange = np.arange(
        start=np.datetime64("1987-10-01 08:00"),
        stop=np.datetime64("1987-10-01 09:01"),
        step=datetime.timedelta(hours=1),
    )
    reference = xr.DataArray(
        data=np.array([6.600006, 6.600006], dtype=np.float32),
        coords=dict(
            time=xr.DataArray(data=timerange),
            lat=xr.DataArray(data=np.float32(52.5)),
            lon=xr.DataArray(data=np.float32(13.5)),
        ),
    )
    reference = reference.swap_dims(dim_0="time")
    assert_equal(result, reference)


def test_query_era5_point_timerange_numpy(era5_temp2m):
    """
    Query indexed ERA5 NWP data within given time range.
    This variant uses an `np.array` for defining time range boundaries.

    While the input dataset contains three records, filtering by
    time range should only yield two records.
    """

    # Define timerange used for querying.
    timerange = np.arange(
        start=np.datetime64("1987-10-01 08:00"),
        stop=np.datetime64("1987-10-01 09:01"),
        step=datetime.timedelta(hours=1),
    )

    # Temperatures for whole slice.
    result = (
        era5_temp2m.query(time=timerange, lat=52.51074, lon=13.43506)
        .kelvin_to_celsius()
        .data
    )
    assert len(result.data) == 2
    assert result.shape == (2,)

    # Verify values and coordinates.
    reference = xr.DataArray(
        data=np.array([6.600006, 6.600006], dtype=np.float32),
        coords=dict(
            time=xr.DataArray(data=timerange),
            lat=xr.DataArray(data=np.float32(52.5)),
            lon=xr.DataArray(data=np.float32(13.5)),
        ),
    )
    reference = reference.swap_dims(dim_0="time")
    assert_equal(result, reference)

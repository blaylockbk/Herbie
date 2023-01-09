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
def era5_temp2m_index():
    nwp = NwpIndex(name=TEMP2M, time_coordinate=TIMERANGE, resolution=0.25)
    if not nwp.path.exists():
        nwp.save(dataset=open_era5_zarr(TEMP2M, 1987, 10, TIMERANGE[0], TIMERANGE[-1]))
    return nwp


def test_query_era5_monterey_fahrenheit_single_spot(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data for a specific point in space and time.
    """

    nwp = era5_temp2m_index.load()

    # Temperatures in Monterey, in Fahrenheit.
    first = (
        nwp.query(time="1987-10-01 08:00", lat=36.6083, lon=-121.8674)
        .kelvin_to_fahrenheit()
        .data
    )

    # Verify values.
    assert first.values == np.array(73.805008, dtype=np.float32)

    # Verify coordinate.
    assert dict(first.coords) == dict(
        time=xr.DataArray(data=np.datetime64("1987-10-01 08:00"), name="time"),
        lat=xr.DataArray(data=np.float32(36.5), name="lat"),
        lon=xr.DataArray(data=np.float32(-121.75), name="lon"),
    )


def test_query_era5_berlin_celsius_location_full_timerange(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data for the whole time range.
    """

    nwp = era5_temp2m_index.load()

    # Temperatures in Berlin, in Celsius.
    result = nwp.query(lat=52.51074, lon=13.43506).kelvin_to_celsius().data

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


def test_query_era5_monterey_fahrenheit_bbox_area(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data for a given area.

    http://bboxfinder.com/
    """

    nwp = era5_temp2m_index.load()

    # Temperatures in Monterey area, in Fahrenheit.
    result = (
        nwp.query(
            time="1987-10-01 08:00",
            lat=(36.450837, 36.700907),
            lon=(-122.166252, -121.655045),
        )
        .kelvin_to_fahrenheit()
        .data
    )

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


def test_query_era5_latitude_slice(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data for a given area along the same longitude coordinates.
    """

    nwp = era5_temp2m_index.load()

    # Temperatures for whole slice.
    result = (
        nwp.query(time="1987-10-01 08:00", lat=None, lon=(-122.166252, -121.655045))
        .kelvin_to_celsius()
        .data
    )

    # Verify coordinates.
    reference = xr.DataArray(
        data=mock.ANY,
        dims=("lat", "lon"),
        coords=dict(
            time=xr.DataArray(data=np.datetime64("1987-10-01 08:00")),
            lat=xr.DataArray(
                data=np.arange(start=90.0, stop=-90.0, step=-0.25, dtype=np.float32),
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
        -43.399993896484375,
        -43.399993896484375,
        -43.399993896484375,
    ]
    assert result[-1].coords["lat"] == -89.75


def test_query_era5_time_slice_tuple(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data within given time range.
    This variant uses a `tuple` for defining time range boundaries.

    While the input dataset contains three records, filtering by
    time range should only yield two records.
    """

    # Load data.
    nwp = era5_temp2m_index.load()

    # Temperatures for whole slice.
    result = (
        nwp.query(
            time=(np.datetime64("1987-10-01 08:00"), np.datetime64("1987-10-01 09:05")),
            lat=52.51074,
            lon=13.43506,
        )
        .kelvin_to_celsius()
        .data
    )

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


def test_query_era5_time_slice_range(era5_temp2m_index):
    """
    Query indexed ERA5 NWP data within given time range.
    This variant uses a `np.array` for defining time range boundaries.

    While the input dataset contains three records, filtering by
    time range should only yield two records.
    """

    # Load data.
    nwp = era5_temp2m_index.load()

    # Define timerange used for querying.
    timerange = np.arange(
        start=np.datetime64("1987-10-01 08:00"),
        stop=np.datetime64("1987-10-01 09:01"),
        step=datetime.timedelta(hours=1),
    )

    # Temperatures for whole slice.
    result = (
        nwp.query(time=timerange, lat=52.51074, lon=13.43506).kelvin_to_celsius().data
    )

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

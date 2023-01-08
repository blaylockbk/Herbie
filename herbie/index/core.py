# MIT License
# (c) 2023 Andreas Motl <andreas.motl@panodata.org>
# https://github.com/earthobservations
import dataclasses
import logging
import os.path
import typing as t
from pathlib import Path

import iarray_community as ia
import numpy as np
import xarray as xr
from ndindex import Slice
from scipy.constants import convert_temperature

from herbie.index.util import dataset_info, round_clipped

logger = logging.getLogger(__name__)


class NwpIndex:
    """
    Manage a multidimensional index of NWP data, using Caterva and ironArray.

    - https://caterva.readthedocs.io/
    - https://ironarray.io/docs/html/
    """

    # Where the ironArray files (`.iarr`) will be stored.
    # FIXME: Segfaults when path contains spaces. => Report to ironArray fame.
    # `/Users/amo/Library/Application Support/herbie/index-iarray/precipitation_amount_1hour_Accumulation.iarr`
    # BASEDIR = platformdirs.user_data_path("herbie").joinpath("index-iarray")

    # Alternatively, just use the working directory for now.
    BASEDIR = Path(os.path.curdir)

    # Default ironArray configuration.
    IA_CONFIG = dict(
        codec=ia.Codec.LZ4,
        clevel=9,
        # How to choose the best numbers?
        # https://ironarray.io/docs/html/tutorials/03.Slicing_Datasets_and_Creating_Views.html#Optimization-Tips
        chunks=(360, 360, 720),
        blocks=(180, 180, 360),
        # chunks=(360, 128, 1440),
        # blocks=(8, 8, 720),
        # TODO: Does it really work?
        # nthreads=12,
    )

    def __init__(self, name, time_coordinate, resolution=None, data=None):
        self.name = name
        self.resolution = resolution
        self.coordinate = Coordinate(time=time_coordinate)
        if self.resolution:
            self.coordinate.mkgrid(resolution=self.resolution)
        self.data: ia.IArray = data
        self.path = self.BASEDIR.joinpath(self.name).with_suffix(".iarr")

    def load(self):
        self.data: ia.IArray = ia.open(str(self.path))
        logger.info(f"Loaded IArray from: {self.path}")
        logger.debug(f"IArray info:\n{self.data.info}")
        return self

    def save(self, dataset: xr.Dataset):
        """
        Derived from ironArray's `fetch_data.py` example program [1,2],
        and its documentation about "Configuring ironArray" [3].

        [1] https://github.com/ironArray/iron-array-notebooks/blob/76fe0e9f93a75443e3aed73a9ffc36119d4aad6c/tutorials/fetch_data.py#L11-L18
        [2] https://github.com/ironArray/iron-array-notebooks/blob/76fe0e9f93a75443e3aed73a9ffc36119d4aad6c/tutorials/fetch_data.py#L37-L41
        [3] https://ironarray.io/docs/html/tutorials/02.Configuring_ironArray.html
        """

        # Use data from first data variable within dataset.
        data_variable = list(dataset.data_vars.keys())[0]
        logger.info(f"Discovered dataset variable: {data_variable}")
        logger.info(f"Storing and indexing to: {self.path}")
        logger.debug(f"Dataset info:\n{dataset_info(dataset)}")

        data = dataset[data_variable]
        logger.info(
            f"Data variable '{data_variable}' has shape={data.shape} and dtype={data.dtype}"
        )
        with ia.config(**self.IA_CONFIG):
            ia_data = ia.empty(
                shape=data.shape, dtype=data.dtype, urlpath=str(self.path)
            )
            logger.info("Populating IArray")
            ia_data[:] = data.values
        logger.info(f"IArray is ready")
        logger.debug(f"IArray info:\n{ia_data.info}")
        self.data = ia_data

    def round_location(self, value):
        return round_clipped(value, self.resolution)

    def query(self, time=None, lat=None, lon=None) -> "Result":

        # Query by point or range (bbox).
        if lat is None:
            idx_lat = np.where(self.coordinate.lat)[0]
            lat_slice = Slice(start=idx_lat[0], stop=idx_lat[-1] + 1)
        elif isinstance(lat, float):
            idx_lat = np.where(self.coordinate.lat == self.round_location(lat))[0][0]
            lat_slice = Slice(start=idx_lat, stop=idx_lat + 2)
        elif isinstance(lat, (t.Sequence, np.ndarray)):
            idx_lat = np.where(
                np.logical_and(
                    self.coordinate.lat >= self.round_location(lat[0]),
                    self.coordinate.lat <= self.round_location(lat[1]),
                )
            )[0]
            lat_slice = Slice(start=idx_lat[0], stop=idx_lat[-1] + 1)
        else:
            raise ValueError(f"Unable to process value for lat={lat}, type={type(lat)}")

        if lon is None:
            idx_lon = np.where(self.coordinate.lon)[0]
            lon_slice = Slice(start=idx_lon[0], stop=idx_lon[-1] + 1)
        elif isinstance(lon, float):
            idx_lon = np.where(self.coordinate.lon == self.round_location(lon))[0][0]
            lon_slice = Slice(start=idx_lon, stop=idx_lon + 2)
        elif isinstance(lon, (t.Sequence, np.ndarray)):
            idx_lon = np.where(
                np.logical_and(
                    self.coordinate.lon >= self.round_location(lon[0]),
                    self.coordinate.lon <= self.round_location(lon[1]),
                )
            )[0]
            lon_slice = Slice(start=idx_lon[0], stop=idx_lon[-1] + 1)
        else:
            raise ValueError(f"Unable to process value for lon={lon}, type={type(lon)}")

        # Optionally query by timestamp, or not.
        if time is None:
            filtered = self.data[:, lat_slice, lon_slice]
            timestamp_coord = self.coordinate.time[:]
        elif isinstance(time, str):
            idx_time = np.where(self.coordinate.time == np.datetime64(time))[0][0]
            time_slice = Slice(idx_time, idx_time + 2)
            filtered = self.data[time_slice, lat_slice, lon_slice]
            timestamp_coord = self.coordinate.time[time_slice.start : time_slice.stop]
        elif isinstance(time, (t.Sequence, np.ndarray)):
            idx_time = np.where(
                np.logical_and(
                    self.coordinate.time >= time[0],
                    self.coordinate.time <= time[1],
                )
            )[0]
            time_slice = Slice(start=idx_time[0], stop=idx_time[-1] + 1)
            filtered = self.data[time_slice, lat_slice, lon_slice]
            timestamp_coord = self.coordinate.time[time_slice.start : time_slice.stop]
        else:
            raise ValueError(
                f"Unable to process value for time={time}, type={type(time)}"
            )

        # Rebuild DataArray from result.
        outdata = xr.DataArray(
            filtered,
            dims=("time", "lat", "lon"),
            coords={
                "lat": self.coordinate.lat[lat_slice.start : lat_slice.stop],
                "lon": self.coordinate.lon[lon_slice.start : lon_slice.stop],
                "time": timestamp_coord,
            },
        )

        return Result(da=outdata)


@dataclasses.dataclass
class Coordinate:
    """
    Manage data for all available coordinates.

    # TODO: How could this meta information be carried over from the source data?
    """

    time: t.Optional[np.ndarray] = None
    lat: t.Optional[np.ndarray] = None
    lon: t.Optional[np.ndarray] = None

    def mkgrid(self, resolution: float):
        self.lat = np.arange(start=90.0, stop=-90.0, step=-resolution, dtype=np.float32)
        self.lon = np.arange(
            start=-180.0, stop=180.0, step=resolution, dtype=np.float32
        )


@dataclasses.dataclass
class Result:
    """
    Wrap query result, and provide convenience accessor methods and value converters.
    """

    da: xr.DataArray

    def select_first(self) -> xr.DataArray:
        return self.da[0][0][0]

    def select_first_point(self):
        return self.da.sel(lat=self.da["lat"][0], lon=self.da["lon"][0])

    def select_first_timestamp(self):
        return self.da.sel(time=self.da["time"][0])

    def kelvin_to_celsius(self):
        self.da.values = convert_temperature(self.da.values, "Kelvin", "Celsius")
        return self

    def kelvin_to_fahrenheit(self):
        self.da.values = convert_temperature(self.da.values, "Kelvin", "Fahrenheit")
        return self

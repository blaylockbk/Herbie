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

from herbie.index.model import DataSchema, QueryParameter
from herbie.index.util import (
    dataset_get_data_variable_names,
    dataset_info,
    is_sequence,
    round_clipped,
)

logger = logging.getLogger(__name__)


class NwpIndex:
    """
    Manage a multidimensional index of NWP data, using Caterva and ironArray.

    - https://caterva.readthedocs.io/
    - https://ironarray.io/docs/html/

    TODO: Think about making this an xarray accessor, e.g. `ds.xindex`.

    - https://docs.xarray.dev/en/stable/internals/extending-xarray.html
    """

    # Where the ironArray files (`.iarr`) will be stored.
    # FIXME: Segfaults when path contains spaces. => Report to ironArray fame.
    # `/Users/amo/Library/Application Support/herbie/index-iarray/precipitation_amount_1hour_Accumulation.iarr`
    # BASEDIR = platformdirs.user_data_path("herbie").joinpath("index-iarray")

    # Alternatively, just use the working directory for now.
    BASEDIR = Path(os.path.curdir)

    # Configure ironArray.
    IA_CONFIG = dict(
        codec=ia.Codec.ZSTD,
        clevel=1,
        # How to choose the best numbers?
        # https://ironarray.io/docs/html/tutorials/03.Slicing_Datasets_and_Creating_Views.html#Optimization-Tips
        chunks=(360, 360, 720),
        blocks=(180, 180, 360),
        # chunks=(360, 128, 1440),
        # blocks=(8, 8, 720),
        # TODO: Does it really work?
        # nthreads=12,
    )

    def __init__(self, name, resolution=None, schema=None, dataset=None, irondata=None):
        self.name: str = name
        self._resolution: float = resolution
        self.dataset: xr.Dataset = dataset
        self.irondata: ia.IArray = irondata

        self.path = self.BASEDIR.joinpath(self.name).with_suffix(".iarr")
        self.schema: DataSchema = schema or DataSchema(path=self.path)

    def exists(self):
        return self.path.exists()

    @property
    def resolution(self):
        if self._resolution:
            return self._resolution
        elif self.schema.ds is not None:
            return self.schema.get_resolution()
        else:
            raise ValueError("Resolution is required for querying the Dataset by geospatial coordinates")

    @resolution.setter
    def resolution(self, value):
        self._resolution = value

    def load(self):
        """
        Load data from ironArray file.
        """

        # Load data.
        # TODO: Handle multiple variable names.
        self.irondata: ia.IArray = ia.open(str(self.path))
        logger.info(f"Loaded IArray from: {self.path}")
        logger.debug(f"IArray info:\n{self.irondata.info}")

        # Load schema.
        self.schema.load()

        return self

    def save(self, dataset: xr.Dataset):
        """
        Save data to ironArray file, effectively indexing it on all dimensions.

        Derived from ironArray's `fetch_data.py` example program [1,2],
        and its documentation about "Configuring ironArray" [3].

        [1] https://github.com/ironArray/iron-array-notebooks/blob/76fe0e9f93a75443e3aed73a9ffc36119d4aad6c/tutorials/fetch_data.py#L11-L18
        [2] https://github.com/ironArray/iron-array-notebooks/blob/76fe0e9f93a75443e3aed73a9ffc36119d4aad6c/tutorials/fetch_data.py#L37-L41
        [3] https://ironarray.io/docs/html/tutorials/02.Configuring_ironArray.html
        """

        # Use data from first data variable within dataset.
        # TODO: Handle multiple variable names.
        data_variables = dataset_get_data_variable_names(dataset)
        data_variable = data_variables[0]
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
        self.irondata = ia_data

        # Save schema.
        self.schema.save(ds=dataset)

    def query(self, time=None, lat=None, lon=None) -> "Result":
        """
        Query ironArray by multiple dimensions.
        """

        # Compute slices for time or time range, and geolocation point or range (bbox).
        time_slice = self.time_slice(coordinate="time", value=time)
        lat_slice = self.geo_slice(coordinate="lat", value=lat)
        lon_slice = self.geo_slice(coordinate="lon", value=lon)

        # Slice data.
        data = self.irondata[time_slice, lat_slice, lon_slice]

        # Rebuild Dataset from result.
        coords = {
            "time": self.schema.ds.coords["time"][time_slice.start: time_slice.stop],
            "lat": self.schema.ds.coords["lat"][lat_slice.start: lat_slice.stop],
            "lon": self.schema.ds.coords["lon"][lon_slice.start: lon_slice.stop],
        }
        ds = self.to_dataset(data, coords=coords)

        return Result(qp=QueryParameter(time=time, lat=lat, lon=lon), ds=ds)

    def to_dataset(self, irondata, coords):
        """
        Re-create Xarray Dataset from ironArray data and coordinates.

        The intention is to emit a Dataset which has the same character
        as the Dataset originally loaded from GRIB/netCDF/HDF5/Zarr.
        """

        # Re-create empty Dataset with original shape.
        schema = self.schema.ds.copy(deep=True)
        dataset = xr.Dataset(data_vars=schema.data_vars, coords=coords, attrs=schema.attrs)

        # Populate data.
        # TODO: Handle more than one variable.
        # TODO: Is there a faster operation than using `list(irondata)`?
        variable0_info = self.schema.metadata["variables"][0]
        variable0_name = variable0_info["name"]
        dataset[variable0_name] = xr.DataArray(list(irondata), **variable0_info)

        return dataset

    def geo_slice(self, coordinate: str, value: t.Union[float, t.Sequence, np.ndarray]):
        """
        Compute slice for geolocation point or range (bbox).
        """

        coord = self.schema.ds.coords[coordinate]

        if value is None:
            idx = np.where(coord)[0]
            effective_slice = Slice(start=idx[0], stop=idx[-1] + 1)
        elif isinstance(value, float):
            idx = np.where(coord == self.round_location(value))[0][0]
            effective_slice = Slice(start=idx, stop=idx + 2)
        elif isinstance(value, (t.Sequence, np.ndarray)):
            idx = np.where(
                np.logical_and(
                    coord >= self.round_location(value[0]),
                    coord <= self.round_location(value[1]),
                )
            )[0]
            effective_slice = Slice(start=idx[0], stop=idx[-1] + 1)
        else:
            raise ValueError(
                f"Unable to process value for {coordinate}={value}, type={type(value)}"
            )

        return effective_slice

    def time_slice(
        self, coordinate: str, value: t.Union[float, t.Sequence, np.ndarray]
    ):
        """
        Compute slice for time or time range.
        """

        coord = self.schema.ds.coords[coordinate]

        if value is None:
            idx = np.where(coord)[0]
            effective_slice = Slice(idx[0], idx[-1] + 1)
        elif isinstance(value, str):
            idx = np.where(coord == np.datetime64(value))[0][0]
            effective_slice = Slice(idx, idx + 2)
        elif isinstance(value, (t.Sequence, np.ndarray)):
            idx = np.where(
                np.logical_and(
                    coord >= np.datetime64(value[0]),
                    coord <= np.datetime64(value[1]),
                )
            )[0]
            effective_slice = Slice(start=idx[0], stop=idx[-1] + 1)
        else:
            raise ValueError(
                f"Unable to process value for {coordinate}={value}, type={type(value)}"
            )

        return effective_slice

    def round_location(self, value):
        return round_clipped(value, self.resolution)


@dataclasses.dataclass
class Result:
    """
    Wrap query result, and provide convenience accessor methods and value converters.
    """

    qp: QueryParameter
    ds: xr.Dataset

    @property
    def pv(self):
        """
        Return primary variable name. That is, the first one.

        # TODO: Handle multiple variable names.
        """
        return list(self.ds.data_vars.keys())[0]

    def select_first(self) -> xr.DataArray:
        return self.ds[self.pv][0][0][0]

    def select_first_point(self):
        da = self.ds[self.pv]
        return da.sel(lat=da["lat"][0], lon=da["lon"][0])

    def select_first_timestamp(self):
        da = self.ds[self.pv]
        return da.sel(time=da["time"][0])

    def kelvin_to_celsius(self):
        da = self.ds[self.pv]
        da.values = convert_temperature(da.values, "Kelvin", "Celsius")
        return self

    def kelvin_to_fahrenheit(self):
        da = self.ds[self.pv]
        da.values = convert_temperature(da.values, "Kelvin", "Fahrenheit")
        return self

    @property
    def data(self) -> xr.DataArray:
        """
        Auto-select shape of return value, based on the shape of the query parameters.
        """
        all_defined = all(
            v is not None for v in [self.qp.time, self.qp.lat, self.qp.lon]
        )
        is_time_range = is_sequence(self.qp.time)
        is_lat_range = is_sequence(self.qp.lat)
        is_lon_range = is_sequence(self.qp.lon)
        if all_defined and not any([is_time_range, is_lat_range, is_lon_range]):
            return self.select_first()
        elif not any([is_lat_range, is_lon_range]):
            return self.select_first_point()
        elif self.qp.time and not is_time_range:
            return self.select_first_timestamp()
        else:
            raise ValueError(
                f"Unable to auto-select shape of return value, "
                f"query parameters have unknown shape: {self.qp}"
            )

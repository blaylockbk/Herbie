# MIT License
# (c) 2023 Andreas Motl <andreas.motl@panodata.org>
# https://github.com/earthobservations
import dataclasses
import json
import typing as t
from pathlib import Path

import xarray as xr

from herbie.index.util import dataset_get_data_variable_names, dataset_without_data


@dataclasses.dataclass
class DataSchema:
    """
    Manage saving and loading an Xarray Dataset schema in netCDF format.

    That means, on saving, all data variables are dropped, but metadata
    information about them is stored alongside the data. This information
    is reused when re-creating the Dataset in the same shape.
    """

    path: Path
    ds: xr.Dataset = None
    metadata: t.Dict = None
    nc_file: Path = dataclasses.field(init=False)
    json_file: Path = dataclasses.field(init=False)

    def __post_init__(self):
        self.nc_file = self.path.joinpath("schema.nc")
        self.json_file = self.path.joinpath("schema.json")

    def load(self):
        """
        Load metadata information for Dataset from netCDF file.
        """
        self.ds = xr.load_dataset(self.nc_file)
        with open(self.json_file, "r") as fp:
            self.metadata = json.load(fp)

    def save(self, ds: xr.Dataset):
        """
        Strip data off Dataset, and save its metadata information into netCDF file.
        """

        self.ds = dataset_without_data(ds)
        self.metadata = self.get_metadata(ds)

        self.ds.to_netcdf(self.nc_file)
        with open(self.json_file, "w") as fp:
            json.dump(self.metadata, fp, indent=2)

    @staticmethod
    def get_metadata(ds: xr.Dataset):
        """
        Get metadata from Dataset.

        This metadata is needed in order to save it for reconstructing the
        complete Dataset later.
        """
        result = []
        data_variables = dataset_get_data_variable_names(ds)
        for variable in data_variables:
            da: xr.DataArray = ds[variable]
            item = {
                "name": da.name,
                "attrs": dict(da.attrs),
                "dims": list(da.dims),
            }
            result.append(item)
        return {"variables": result}

    def get_resolution(self):
        """
        Derive resolution of grid from coordinates.
        """
        lat_coord = self.ds.coords["lat"]
        lon_coord = self.ds.coords["lon"]
        lat_delta = lat_coord[1].values - lat_coord[0].values
        lon_delta = lon_coord[1].values - lon_coord[0].values
        if abs(lat_delta) == abs(lon_delta):
            return abs(lat_delta)
        else:
            raise ValueError(
                "Resolution computed from coordinates deviates between latitude and longitude"
            )


@dataclasses.dataclass
class QueryParameter:
    """
    Manage query parameters.
    """

    time: t.Optional[str] = None
    lat: t.Optional[float] = None
    lon: t.Optional[float] = None

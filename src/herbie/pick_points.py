"""Grid interpolation utilities for extracting point values from 2D grids.

This module provides functionality to extract values at specific lat/lon points
from gridded datasets using nearest neighbor or distance-weighted interpolation.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import xarray as xr

try:
    from sklearn.neighbors import BallTree

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class GridPointPicker:
    """Extract point values from 2D gridded datasets using spatial indexing.

    This class handles the core logic for finding and extracting values at
    specified lat/lon points from xarray Datasets using BallTree spatial indexing.
    """

    EARTH_RADIUS_KM = 6371

    def __init__(
        self,
        ds: xr.Dataset,
        cache_dir: Path | None = None,
        tree_name: str | None = None,
    ):
        """Initialize the point picker with a dataset.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset containing gridded data
        cache_dir : Path, optional
            Directory for caching BallTree objects
        tree_name : str, optional
            Name for the BallTree cache file
        """
        if not SKLEARN_AVAILABLE:
            raise ModuleNotFoundError(
                "scikit-learn is required. Install with: "
                "`pip install scikit-learn` or `pip install 'herbie-data[extras]'`"
            )

        self.ds = ds
        self.cache_dir = cache_dir
        self.tree_name = tree_name or getattr(ds, "model", None)

        # Prepare grid data once
        self._prepare_dataset()
        self.df_grid = self._create_grid_dataframe()

    def pick_points(
        self,
        points: pd.DataFrame,
        method: Literal["nearest", "weighted"] = "nearest",
        k: int | None = None,
        max_distance: float = 500,
        use_cached_tree: bool | Literal["replant"] = True,
    ) -> xr.Dataset:
        """Pick grid values at specified points.

        Parameters
        ----------
        points : pd.DataFrame
            DataFrame with 'latitude' and 'longitude' columns
        method : {'nearest', 'weighted'}
            Interpolation method
        k : int, optional
            Number of nearest neighbors (defaults: 1 for nearest, 4 for weighted)
        max_distance : float
            Maximum distance in km for valid neighbors (default: 500)
        use_cached_tree : bool or 'replant'
            Whether to use cached BallTree

        Returns
        -------
        xr.Dataset
            Dataset with values at requested points
        """
        # Validate and prepare
        validate_points(points)
        k = determine_k(method, k)

        # Get spatial index
        tree = self._get_ball_tree(use_cached_tree)

        # Query nearest neighbors
        dist, ind = tree.query(np.deg2rad(points[["latitude", "longitude"]]), k=k)
        dist *= self.EARTH_RADIUS_KM

        # Extract point values
        k_points = self._extract_k_points(points, dist, ind, k, max_distance)

        # Aggregate results
        return aggregate_results(k_points, method, k)

    def _prepare_dataset(self) -> None:
        """Prepare dataset by standardizing dimension names."""
        # Only keep variables with dimensions
        self.ds = self.ds[[v for v in self.ds if self.ds[v].dims != ()]]

        # Standardize lat/lon dimension names if they exist
        rename_map = {}
        if "latitude" in self.ds.dims:
            rename_map["latitude"] = "y"
        if "longitude" in self.ds.dims:
            rename_map["longitude"] = "x"

        if rename_map:
            self.ds = self.ds.rename_dims(rename_map)

    def _create_grid_dataframe(self) -> pd.DataFrame:
        """Create DataFrame of grid lat/lon coordinates."""
        # Get lat/lon coordinates with flexible naming
        lat_da = get_coordinate(self.ds, ["latitude", "lat"])
        lon_da = get_coordinate(self.ds, ["longitude", "lon"])

        # Broadcast to ensure same dimensions
        lat_da, lon_da = xr.broadcast(lat_da, lon_da)

        # Standardize names
        if lat_da.name != "latitude":
            lat_da = lat_da.rename("latitude")
        if lon_da.name != "longitude":
            lon_da = lon_da.rename("longitude")

        # Create grid dataset
        grid_ds = xr.Dataset({"latitude": lat_da, "longitude": lon_da})

        # Convert to dataframe, dropping scalar coordinates
        df_grid = grid_ds.drop_vars(
            [name for name, coord in grid_ds.coords.items() if not coord.ndim]
        ).to_dataframe()[["latitude", "longitude"]]

        return df_grid

    def _get_ball_tree(self, use_cached_tree: bool | Literal["replant"]) -> BallTree:
        """Get BallTree, from cache or newly created."""
        # Determine cache path
        cache_path = None
        if use_cached_tree and self.cache_dir and self.tree_name:
            grid_size = f"{self.ds.x.size}-{self.ds.y.size}"
            cache_path = (
                self.cache_dir / "BallTree" / f"{self.tree_name}_{grid_size}.pkl"
            )
        elif use_cached_tree and not self.tree_name:
            print(
                "WARNING: BallTree caching disabled - tree_name not specified.\n"
                "         Provide tree_name parameter to enable caching."
            )
            use_cached_tree = False

        # No caching requested
        if not use_cached_tree:
            return create_ball_tree(self.df_grid)

        # Replant or doesn't exist
        if use_cached_tree == "replant" or not cache_path.exists():
            tree = create_ball_tree(self.df_grid, save_to=cache_path)
            return tree

        # Load from cache
        tree = load_ball_tree(cache_path)

        # Validate cache matches grid
        if hasattr(tree, "data") and tree.data is not None:
            if len(tree.data) != len(self.df_grid):
                print("INFO: Cached BallTree size mismatch, recreating...")
                tree = create_ball_tree(self.df_grid, save_to=cache_path)

        return tree

    def _extract_k_points(
        self,
        points: pd.DataFrame,
        dist: np.ndarray,
        ind: np.ndarray,
        k: int,
        max_distance: float,
    ) -> list[xr.Dataset]:
        """Extract grid values for k nearest neighbors."""
        k_points = []
        df_grid_reset = self.df_grid.reset_index()

        for i in range(k):
            # Prepare point metadata
            point_data = prepare_point_data(
                points, df_grid_reset, dist[:, i], ind[:, i], max_distance
            )

            # Skip if all points were filtered out
            if len(point_data) == 0:
                continue

            # Select grid points
            ds_points = self.ds.sel(
                x=point_data.x_grid.to_xarray().dropna("point").astype("int"),
                y=point_data.y_grid.to_xarray().dropna("point").astype("int"),
            )

            # Add point metadata as coordinates
            ds_points = add_point_coordinates(ds_points, point_data, points.columns)

            k_points.append(ds_points.drop_vars("point"))

        return k_points


# Standalone utility functions


def validate_points(points: pd.DataFrame) -> None:
    """Validate that points DataFrame has required columns and valid values."""
    if "latitude" not in points or "longitude" not in points:
        raise ValueError(
            "points DataFrame must have 'latitude' and 'longitude' columns"
        )

    if not points.latitude.between(-90, 90, inclusive="both").all():
        invalid_lats = points.latitude[
            ~points.latitude.between(-90, 90, inclusive="both")
        ]
        raise ValueError(
            f"All latitude values must be in range [-90, 90]. "
            f"Found invalid values: {invalid_lats.tolist()}"
        )

    lon_valid = (
        points.longitude.between(0, 360, inclusive="both").all()
        or points.longitude.between(-180, 180, inclusive="both").all()
    )
    if not lon_valid:
        raise ValueError(
            "All longitude values must be in range [-180, 180] or [0, 360]. "
            "Mixed ranges or out-of-range values detected."
        )


def determine_k(method: str, k: int | None) -> int:
    """Determine number of nearest neighbors based on method."""
    if k is not None:
        if not isinstance(k, int) or k < 1:
            raise ValueError("k must be a positive integer or None")
        return k

    return 1 if method == "nearest" else 4


def get_coordinate(ds: xr.Dataset, names: list[str]) -> xr.DataArray:
    """Get coordinate from dataset, trying multiple possible names."""
    for name in names:
        if name in ds.variables:
            return ds[name]
    raise KeyError(
        f"Dataset must contain one of {names}. "
        f"Available variables: {list(ds.variables)}"
    )


def create_ball_tree(
    df_grid: pd.DataFrame,
    save_to: Path | None = None,
) -> BallTree:
    """Create BallTree from grid coordinates."""
    timer = pd.Timestamp("now")
    print("INFO: 🌱 Growing new BallTree...", end="", flush=True)

    tree = BallTree(np.deg2rad(df_grid), metric="haversine")

    elapsed = (pd.Timestamp("now") - timer).total_seconds()
    print(f"🌳 Complete in {elapsed:.2f}s")

    if save_to:
        try:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            with open(save_to, "wb") as f:
                pickle.dump(tree, f)
            print(f"INFO: Saved BallTree to {save_to}")
        except OSError as e:
            print(f"WARNING: Could not save BallTree: {e}")

    return tree


def load_ball_tree(path: Path) -> BallTree:
    """Load BallTree from pickle file."""
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        raise RuntimeError(f"Failed to load BallTree from {path}: {e}")


def prepare_point_data(
    points: pd.DataFrame,
    df_grid: pd.DataFrame,
    distances: np.ndarray,
    indices: np.ndarray,
    max_distance: float,
) -> pd.DataFrame:
    """Prepare point metadata and filter by distance threshold."""
    point_data = points.copy()
    point_data["point_grid_distance"] = distances
    point_data["grid_index"] = indices

    # Merge with grid coordinates
    point_data = pd.concat(
        [
            point_data.reset_index(drop=True),
            df_grid.iloc[indices].add_suffix("_grid").reset_index(drop=True),
        ],
        axis=1,
    )
    point_data.index.name = "point"

    # Filter by max distance
    if max_distance > 0:
        mask = point_data.point_grid_distance <= max_distance
        flagged = point_data[~mask]

        if len(flagged) > 0:
            print(
                f"WARNING: Removed {len(flagged)} point(s) "
                f"exceeding {max_distance} km threshold"
            )
            print(flagged[["latitude", "longitude", "point_grid_distance"]])

        point_data = point_data[mask]

    return point_data


def add_point_coordinates(
    ds: xr.Dataset,
    point_data: pd.DataFrame,
    point_columns: pd.Index,
) -> xr.Dataset:
    """Add point metadata as coordinates to dataset."""
    # Add distance coordinate
    ds.coords["point_grid_distance"] = point_data.point_grid_distance.to_xarray()
    ds["point_grid_distance"].attrs.update(
        {
            "long_name": "Distance between requested point and nearest grid point",
            "units": "km",
        }
    )

    # Add all point columns as coordinates
    for col in point_columns:
        coord_name = f"point_{col}"
        ds.coords[coord_name] = point_data[col].to_xarray()
        ds[coord_name].attrs["long_name"] = f"Requested point {col}"

    return ds


def aggregate_results(
    k_points: list[xr.Dataset],
    method: str,
    k: int,
) -> xr.Dataset:
    """Aggregate k-nearest neighbor results based on method."""
    if not k_points:
        raise ValueError(
            "No valid points found after filtering. "
            "All points may exceed max_distance threshold."
        )

    if method == "nearest":
        return k_points[0] if k == 1 else xr.concat(k_points, dim="k")

    if method == "weighted":
        return compute_weighted_mean(k_points)

    raise ValueError(f"Invalid method '{method}'. Must be 'nearest' or 'weighted'.")


def compute_weighted_mean(k_points: list[xr.Dataset]) -> xr.Dataset:
    """Compute inverse-distance weighted mean from k nearest points.

    Returns weighted mean values for data variables, but preserves the k dimension
    for latitude, longitude, and point_grid_distance coordinates to show which
    grid points were used in the interpolation.

    Special handling for zero-distance cases: if a point is exactly on a grid point,
    use that grid point's value without weighted averaging.
    """
    combined = xr.concat(k_points, dim="k")

    # Get or reconstruct distance coordinate
    distance_coord = combined.coords.get("point_grid_distance")

    if distance_coord is None:
        raise ValueError("point_grid_distance coordinate missing")

    # Handle case where k dimension was dropped during concat
    if "k" not in distance_coord.dims:
        distance_coord = xr.concat(
            [
                kp.coords["point_grid_distance"].expand_dims(k=[idx])
                for idx, kp in enumerate(k_points)
            ],
            dim="k",
        )
        combined = combined.assign_coords(point_grid_distance=distance_coord)
        distance_coord = combined.coords["point_grid_distance"]

    # Handle zero-distance case: use exact grid point value
    min_distance = distance_coord.min(dim="k")
    is_exact_match = min_distance < 1e-10  # threshold for "zero" distance

    # Compute inverse-distance weights
    # For zero distances, we'll handle them separately, so clip to avoid inf
    weights = xr.where(
        distance_coord < 1e-10,
        1.0,  # Temporary placeholder
        1.0 / distance_coord,
    )

    # For exact matches, set weight to 1 for closest point, 0 for others
    if is_exact_match.any():
        # Find which k index has minimum distance
        k_min = distance_coord.argmin(dim="k")
        # Create mask: True only for the minimum distance point
        exact_mask = (
            xr.DataArray(np.arange(len(k_points)), dims=["k"], coords={"k": combined.k})
            == k_min
        )
        # Override weights for exact match cases
        weights = xr.where(is_exact_match, exact_mask.astype(float), weights)

    # Compute weighted average for DATA VARIABLES (reduces k dimension)
    sum_of_weights = weights.sum(dim="k")

    # Build result dataset with only data variables reduced
    result_data_vars = {}
    for var_name in combined.data_vars:
        weighted_sum = (combined[var_name] * weights).sum(dim="k")
        result_data_vars[var_name] = weighted_sum / sum_of_weights

    result = xr.Dataset(result_data_vars)

    # Copy coordinates that don't have 'k' dimension
    for coord_name, coord_val in combined.coords.items():
        if coord_name in result.coords:
            continue  # Already exists
        if "k" not in coord_val.dims:
            result.coords[coord_name] = coord_val

    # Keep lat/lon/distance WITH the k dimension to show which points were used
    if "latitude" in combined.coords:
        result.coords["latitude"] = combined.coords["latitude"]

    if "longitude" in combined.coords:
        result.coords["longitude"] = combined.coords["longitude"]

    if "point_grid_distance" in combined.coords:
        result.coords["point_grid_distance"] = combined.coords["point_grid_distance"]

    result.attrs["pick_point_method"] = "weighted"
    result.attrs["pick_point_k"] = len(k_points)

    return result

"""Test the ds.herbie.pick_points() accessor."""

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from herbie import Herbie

# Test datasets
ds1 = Herbie("2024-03-01 00:00", model="hrrr").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds2 = Herbie("2024-03-01 00:00", model="hrrr").xarray("[U|V]GRD:10 m above")
ds3 = Herbie("2024-03-01 00:00", model="gfs").xarray("TMP:[5,6,7,8,9][0,5]0 mb")
ds4 = Herbie("2024-03-01 00:00", model="gfs").xarray("[U|V]GRD:10 m above")


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between points in km."""
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c


class TestPickPointsBasic:
    """Basic functionality tests."""

    @pytest.mark.parametrize("ds", [ds1, ds2, ds3, ds4])
    def test_nearest_method(self, ds):
        """Test nearest neighbor method returns correct structure."""
        points = pd.DataFrame(
            {
                "longitude": [-100, -105, -98.4],
                "latitude": [40, 29, 42.3],
                "stid": ["aa", "bb", "cc"],
            }
        )

        # Since our test points are in [-180,180] convention
        ds = ds.herbie.to_180()

        result = ds.herbie.pick_points(points, method="nearest")

        # Check dimensions
        assert "point" in result.dims
        assert result.sizes["point"] == len(points)

        # Check coordinates exist
        assert "point_latitude" in result.coords
        assert "point_longitude" in result.coords
        assert "point_grid_distance" in result.coords
        assert "point_stid" in result.coords

        # Check that we got actual lat/lon grid values
        assert "latitude" in result.coords
        assert "longitude" in result.coords

        # Test that picked coordinates are close to requested
        # (within model resolution tolerance)
        np.testing.assert_allclose(
            result.longitude.values,
            result.point_longitude.values,
            atol=1.0,  # Within 1 degree for most models
            rtol=0,
        )

        np.testing.assert_allclose(
            result.latitude.values,
            result.point_latitude.values,
            atol=1.0,
            rtol=0,
        )

    @pytest.mark.parametrize("ds", [ds1, ds2, ds3, ds4])
    def test_weighted_method(self, ds):
        """Test weighted method returns correct structure."""
        points = pd.DataFrame(
            {
                "longitude": [-100, -105, -98.4],
                "latitude": [40, 29, 42.3],
                "stid": ["aa", "bb", "cc"],
            }
        )

        ds = ds.herbie.to_180()
        result = ds.herbie.pick_points(points, method="weighted")

        # Check structure - data is reduced but k dimension preserved for metadata
        assert result.sizes["point"] == len(points)
        assert "k" in result.dims  # k dimension should exist for lat/lon/distance

        # Data variables should NOT have k dimension (they're averaged)
        for var in result.data_vars:
            assert "k" not in result[var].dims, f"Data variable {var} should not have k dimension"

        # But coordinates should have k dimension to show which points were used
        assert "k" in result.coords["latitude"].dims
        assert "k" in result.coords["longitude"].dims
        assert "k" in result.coords["point_grid_distance"].dims

        # Check other coordinates exist (without k)
        assert "point_latitude" in result.coords
        assert "point_longitude" in result.coords
        assert "k" not in result.coords["point_latitude"].dims

        # Test that picked coordinates are close to requested
        # For weighted method, check that ALL k neighbors are within reasonable distance
        # The closest neighbor (k=0) should be very close
        for i in range(len(points)):
            requested_lat = result.point_latitude.isel(point=i).item()
            requested_lon = result.point_longitude.isel(point=i).item()

            # Check the closest grid point (first k neighbor)
            closest_lat = result.latitude.isel(point=i, k=0).item()
            closest_lon = result.longitude.isel(point=i, k=0).item()

            np.testing.assert_allclose(
                closest_lon,
                requested_lon,
                atol=1.0,  # Within 1 degree for most models
                rtol=0,
            )

            np.testing.assert_allclose(
                closest_lat,
                requested_lat,
                atol=1.0,
                rtol=0,
            )
    @pytest.mark.parametrize("ds", [ds1, ds2, ds3, ds4])
    def test_nearest_with_k(self, ds):
        """Test nearest with multiple k values."""
        points = pd.DataFrame(
            {
                "longitude": [-100, -105],
                "latitude": [40, 29],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest", k=4)

        # Should have k dimension
        assert "k" in result.dims
        assert result.sizes["k"] == 4
        assert result.sizes["point"] == len(points)

    @pytest.mark.parametrize("ds", [ds1, ds2, ds3, ds4])
    def test_weighted_with_k(self, ds):
        """Test weighted with custom k value."""
        points = pd.DataFrame(
            {
                "longitude": [-100, -105],
                "latitude": [40, 29],
            }
        )

        result = ds.herbie.pick_points(points, method="weighted", k=8)

        # Data variables should NOT have k dimension (they're averaged)
        for var in result.data_vars:
            assert "k" not in result[var].dims, (
                f"Data variable {var} should not have k dimension"
            )

        # But coordinates should have k dimension to show which points were used
        assert "k" in result.coords["latitude"].dims
        assert "k" in result.coords["longitude"].dims
        assert "k" in result.coords["point_grid_distance"].dims

        # Check other coordinates exist (without k)
        assert "point_latitude" in result.coords
        assert "point_longitude" in result.coords
        assert "k" not in result.coords["point_latitude"].dims

        assert result.sizes["point"] == len(points)


class TestPickPointsCorrectness:
    """Test correctness of interpolation results."""

    def test_simple_grid_exact_match(self):
        """Test that exact grid points return correct values."""
        ds = xr.Dataset(
            {"a": (["latitude", "longitude"], [[1, 2], [3, 4]])},
            coords={
                "latitude": (["latitude"], [45, 46]),
                "longitude": (["longitude"], [100, 101]),
            },
        )

        # Query exact grid points
        points = pd.DataFrame(
            {
                "latitude": [45, 46, 45, 46],
                "longitude": [100, 100, 101, 101],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest", k=1)

        # Should get exact values
        expected_values = [1, 3, 2, 4]
        np.testing.assert_array_equal(result.a.values, expected_values)

        # Distance should be very small (numerical precision)
        assert np.all(result.point_grid_distance < 0.01)

    def test_simple_grid_nearest(self):
        """Test nearest neighbor selection."""
        ds = xr.Dataset(
            {"a": (["latitude", "longitude"], [[1, 0], [0, 0]])},
            coords={
                "latitude": (["latitude"], [45, 46]),
                "longitude": (["longitude"], [100, 101]),
            },
        )

        # Point closer to (45, 100)
        point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]})

        result = ds.herbie.pick_points(point, method="nearest", k=1)

        # Should select grid point at (45, 100) with value 1
        assert result.a.item() == 1
        assert result.latitude.item() == 45
        assert result.longitude.item() == 100

        # Check distance calculation
        expected_dist = haversine_distance(45.25, 100.25, 45, 100)
        np.testing.assert_almost_equal(
            result.point_grid_distance.item(), expected_dist, decimal=1
        )

    def test_coordinate_proximity_hrrr(self):
        """Test that picked coordinates are close to requested for HRRR."""
        ds = ds1  # HRRR data

        points = pd.DataFrame(
            {
                "longitude": [-100, -105, -98.4],
                "latitude": [40, 29, 42.3],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest")

        # For HRRR (~3km resolution), coordinates should be within ~5km
        for i in range(len(points)):
            requested_lat = result.point_latitude.isel(point=i).item()
            requested_lon = result.point_longitude.isel(point=i).item()
            actual_lat = result.latitude.isel(point=i).item()
            actual_lon = result.longitude.isel(point=i).item()

            dist = haversine_distance(
                requested_lat, requested_lon, actual_lat, actual_lon
            )

            # Should be very close for high-resolution model
            assert dist < 5, f"Point {i}: distance {dist} km exceeds 5 km"

    def test_coordinate_proximity_gfs(self):
        """Test that picked coordinates are reasonable for GFS."""
        ds = ds3  # GFS data

        points = pd.DataFrame(
            {
                "longitude": [-100, -105, -98.4],
                "latitude": [40, 29, 42.3],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest")

        # For GFS (~25km resolution), allow larger tolerance
        for i in range(len(points)):
            requested_lat = result.point_latitude.isel(point=i).item()
            requested_lon = result.point_longitude.isel(point=i).item()
            actual_lat = result.latitude.isel(point=i).item()
            actual_lon = result.longitude.isel(point=i).item()

            # Lat/lon should be within ~1 degree for 0.25 degree grid
            assert abs(actual_lat - requested_lat) < 1.5
            assert abs(actual_lon - requested_lon) < 1.5

    def test_weighted_vs_nearest_relationship(self):
        """Test that weighted interpolation is reasonable vs nearest."""
        ds = xr.Dataset(
            {"a": (["latitude", "longitude"], [[10, 20], [30, 40]])},
            coords={
                "latitude": (["latitude"], [45, 46]),
                "longitude": (["longitude"], [100, 101]),
            },
        )

        # Point in center should give weighted average
        point = pd.DataFrame({"latitude": [45.5], "longitude": [100.5]})

        nearest = ds.herbie.pick_points(point, method="nearest", k=1)
        weighted = ds.herbie.pick_points(point, method="weighted", k=4)

        # Weighted should be approximately the mean of all 4 corners
        # (not exactly due to inverse distance weighting)
        expected_mean = 25  # (10+20+30+40)/4

        # Weighted should be closer to mean than any single nearest neighbor
        weighted_val = weighted.a.item()
        nearest_val = nearest.a.item()

        assert abs(weighted_val - expected_mean) < abs(nearest_val - expected_mean)

    def test_distance_monotonicity(self):
        """Test that k-nearest distances are monotonically increasing."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100, -105],
                "latitude": [40, 29],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest", k=5)

        # For each point, distances should increase with k
        for i in range(result.sizes["point"]):
            distances = result.point_grid_distance.isel(point=i).values

            # Check monotonic increase (with small tolerance for numerical precision)
            assert np.all(np.diff(distances) >= -1e-10), (
                f"Distances not monotonic for point {i}: {distances}"
            )


class TestPickPointsEdgeCases:
    """Test edge cases and error conditions."""

    def test_max_distance_filtering(self):
        """Test that max_distance filters out distant points."""
        ds = ds1

        # Point way off the grid
        points = pd.DataFrame(
            {
                "longitude": [-100, 0],  # 0 longitude is far from HRRR grid
                "latitude": [40, 40],
            }
        )

        result = ds.herbie.pick_points(
            points,
            method="nearest",
            max_distance=100,  # Very restrictive
        )

        # Should have fewer points or warning printed
        assert result.sizes["point"] <= len(points)

    def test_nans_in_grid(self):
        """Test handling of NaN values in grid."""
        ds = xr.Dataset(
            {
                "a": (
                    ["latitude", "longitude"],
                    [[1, 0, np.nan], [0, 0, np.nan], [0, 1, np.nan]],
                )
            },
            coords={
                "latitude": (["latitude"], [45, 46, 47]),
                "longitude": (["longitude"], [100, 101, 102]),
            },
        )

        point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]})

        result = ds.herbie.pick_points(point, method="nearest", k=1)

        # Should still work, just pick nearest valid point
        assert not np.isnan(result.a.item())

    def test_dataframe_index_independence(self):
        """Test that non-standard DataFrame indices don't break things."""
        ds = xr.Dataset(
            {"a": (["latitude", "longitude"], [[1, 0], [0, 0]])},
            coords={
                "latitude": (["latitude"], [45, 46]),
                "longitude": (["longitude"], [100, 101]),
            },
        )

        # Non-standard index
        point = pd.DataFrame({"latitude": [45.25], "longitude": [100.25]}, index=[999])

        result = ds.herbie.pick_points(point, method="nearest", k=1)

        # Should work fine
        assert result.a.item() == 1

    def test_self_points_zero_distance(self):
        """Test that model's own grid points have zero distance."""
        H = Herbie("2024-03-01", model="hrrr")
        ds = H.xarray(":TMP:2 m")

        # Sample actual grid points
        n = 50
        points_self = (
            ds[["latitude", "longitude"]]
            .to_dataframe()[["latitude", "longitude"]]
            .sample(n, random_state=42)
            .reset_index(drop=True)
        )

        result = ds.herbie.pick_points(points_self, method="nearest")

        # All distances should be zero (or very close)
        assert np.all(result.point_grid_distance < 0.01)

        # Coordinates should match exactly
        np.testing.assert_allclose(
            result.point_latitude.values, result.latitude.values, rtol=1e-10
        )
        np.testing.assert_allclose(
            result.point_longitude.values, result.longitude.values, rtol=1e-10
        )

    def test_invalid_latitude(self):
        """Test that invalid latitude raises error."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100],
                "latitude": [95],  # Invalid
            }
        )

        with pytest.raises(ValueError, match="latitude.*range"):
            ds.herbie.pick_points(points, method="nearest")

    def test_invalid_longitude(self):
        """Test that invalid longitude raises error."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [400],  # Invalid
                "latitude": [40],
            }
        )

        with pytest.raises(ValueError, match="longitude.*range"):
            ds.herbie.pick_points(points, method="nearest")

    def test_missing_required_columns(self):
        """Test that missing lat/lon columns raises error."""
        ds = ds1

        points = pd.DataFrame(
            {
                "latitude": [40],
                # Missing longitude
            }
        )

        with pytest.raises(ValueError, match="latitude.*longitude"):
            ds.herbie.pick_points(points, method="nearest")

    def test_invalid_method(self):
        """Test that invalid method raises error."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100],
                "latitude": [40],
            }
        )

        with pytest.raises(ValueError, match="method"):
            ds.herbie.pick_points(points, method="invalid")

    def test_invalid_k(self):
        """Test that invalid k raises error."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100],
                "latitude": [40],
            }
        )

        with pytest.raises(ValueError, match="positive integer"):
            ds.herbie.pick_points(points, method="nearest", k=-1)

        with pytest.raises(ValueError, match="positive integer"):
            ds.herbie.pick_points(points, method="nearest", k=0)


class TestPickPointsDataTypes:
    """Test various data types and structures."""

    def test_extra_columns_preserved(self):
        """Test that extra columns in points DataFrame are preserved."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100, -105],
                "latitude": [40, 29],
                "stid": ["station1", "station2"],
                "elevation": [1000, 2000],
                "name": ["Site A", "Site B"],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest")

        # Check all columns preserved as coordinates
        assert "point_stid" in result.coords
        assert "point_elevation" in result.coords
        assert "point_name" in result.coords

        # Check values match
        assert list(result.point_stid.values) == ["station1", "station2"]
        assert list(result.point_elevation.values) == [1000, 2000]

    def test_to_dataframe_conversion(self):
        """Test that result can be converted to DataFrame."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100, -105],
                "latitude": [40, 29],
                "stid": ["aa", "bb"],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest")

        # Should convert without error
        df = result.to_dataframe()

        assert isinstance(df, pd.DataFrame)

    def test_swap_dims_by_stid(self):
        """Test swapping dimension to station ID."""
        ds = ds1

        points = pd.DataFrame(
            {
                "longitude": [-100, -105, -98],
                "latitude": [40, 29, 42],
                "stid": ["KSLC", "KHOU", "KORD"],
            }
        )

        result = ds.herbie.pick_points(points, method="nearest")

        # Swap dimensions
        result_by_stid = result.swap_dims({"point": "point_stid"})

        # Should be indexable by station ID
        assert "point_stid" in result_by_stid.dims

        # Can select by station
        kslc = result_by_stid.sel(point_stid="KSLC")
        assert kslc.point_latitude.item() == 40


class TestPickPointsCaching:
    """Test BallTree caching functionality."""

    def test_cache_reuse(self, tmp_path):
        """Test that cache is reused on subsequent calls."""
        # Create temporary config
        import herbie

        original_save_dir = herbie.config["default"]["save_dir"]
        herbie.config["default"]["save_dir"] = tmp_path

        try:
            ds = ds1  # HRRR temperature data
            points = pd.DataFrame(
                {
                    "longitude": [-100],
                    "latitude": [40],
                }
            )

            # First call - should create cache
            result1 = ds.herbie.pick_points(
                points, method="nearest", use_cached_tree=True, tree_name="test_model"
            )

            # Check cache file exists
            cache_files = list((tmp_path / "BallTree").glob("*.pkl"))
            assert len(cache_files) > 0, "Cache file should have been created"

            # Second call - should use cache
            result2 = ds.herbie.pick_points(
                points, method="nearest", use_cached_tree=True, tree_name="test_model"
            )

            # Results should be identical
            # Get first data variable from the dataset (whatever it is)
            var_name = list(result1.data_vars)[0]

            np.testing.assert_equal(
                result1[var_name].values,
                result2[var_name].values,
                err_msg=f"Results differ for variable {var_name}"
            )

            # Also check that coordinates match
            np.testing.assert_equal(result1.latitude.values, result2.latitude.values)
            np.testing.assert_equal(result1.longitude.values, result2.longitude.values)
            np.testing.assert_equal(
                result1.point_grid_distance.values,
                result2.point_grid_distance.values
            )

        finally:
            herbie.config["default"]["save_dir"] = original_save_dir

    def test_replant_option(self, tmp_path):
        """Test that replant forces recreation of cache."""
        import herbie

        original_save_dir = herbie.config["default"]["save_dir"]
        herbie.config["default"]["save_dir"] = tmp_path

        try:
            ds = ds1
            points = pd.DataFrame(
                {
                    "longitude": [-100],
                    "latitude": [40],
                }
            )

            # Create initial cache
            ds.herbie.pick_points(
                points, method="nearest", use_cached_tree=True, tree_name="test_replant"
            )

            cache_file = list((tmp_path / "BallTree").glob("test_replant*.pkl"))[0]
            initial_mtime = cache_file.stat().st_mtime

            import time

            time.sleep(0.1)  # Ensure different timestamp

            # Replant
            ds.herbie.pick_points(
                points,
                method="nearest",
                use_cached_tree="replant",
                tree_name="test_replant",
            )

            # Cache file should be newer
            new_mtime = cache_file.stat().st_mtime
            assert new_mtime > initial_mtime
        finally:
            herbie.config["default"]["save_dir"] = original_save_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

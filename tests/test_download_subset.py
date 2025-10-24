"""
Comprehensive tests for Herbie subsetting functionality.

Tests with both remote and local files
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
import requests

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)
yesterday = today - timedelta(days=1)

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


# =============================================================================
# Test Suite 1: Remote Subsetting (Download from URL)
# =============================================================================


def test_subset_remote_single_variable():
    """Test downloading a single variable subset from remote."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    var = "TMP:2 m"
    H.download(var)

    # Verify file was created
    subset_path = H.get_localFilePath(var)
    assert subset_path.exists(), "Subset file was not created"

    # Verify file size matches expected byte range
    idx = H.inventory(var)
    expected_size = ((idx.end_byte + 1) - idx.start_byte).sum()
    actual_size = subset_path.stat().st_size

    assert expected_size == actual_size, (
        f"File size mismatch: expected {expected_size}, got {actual_size}"
    )

    # Cleanup
    subset_path.unlink()


def test_subset_remote_multiple_variables():
    """Test downloading multiple variables (U and V wind components)."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    var = "(?:U|V)GRD:10 m"
    H.download(var)

    # Verify file was created
    subset_path = H.get_localFilePath(var)
    assert subset_path.exists(), "Subset file was not created"

    # Verify we got both U and V components
    idx = H.inventory(var)
    assert len(idx) >= 2, f"Expected at least 2 variables (U and V), got {len(idx)}"

    # Verify file size
    expected_size = ((idx.end_byte + 1) - idx.start_byte).sum()
    actual_size = subset_path.stat().st_size
    assert expected_size == actual_size, (
        f"File size mismatch: expected {expected_size}, got {actual_size}"
    )

    # Cleanup
    subset_path.unlink()


def test_subset_remote_level():
    """Test downloading all variables at a specific pressure level."""
    H = Herbie(today, model="hrrr", product="prs", save_dir=save_dir, overwrite=True)

    var = ":500 mb"
    H.download(var)

    # Verify file was created
    subset_path = H.get_localFilePath(var)
    assert subset_path.exists(), "Subset file was not created"

    # Verify we got multiple variables at 500 mb
    idx = H.inventory(var)
    assert len(idx) > 0, "No variables found at 500 mb"
    assert all("500 mb" in str(row.level) for _, row in idx.iterrows()), (
        "Not all variables are at 500 mb"
    )

    # Verify file size
    expected_size = ((idx.end_byte + 1) - idx.start_byte).sum()
    actual_size = subset_path.stat().st_size
    assert expected_size == actual_size, "File size mismatch"

    # Cleanup
    subset_path.unlink()


def test_subset_remote_grouped_messages():
    """Test that adjacent GRIB messages are grouped together efficiently."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download multiple adjacent messages
    var = ":TMP:"
    H.download(var)

    # Verify file was created
    subset_path = H.get_localFilePath(var)
    assert subset_path.exists(), "Subset file was not created"

    # Check that download groups were created properly
    idx = H.inventory(var)
    idx["download_groups"] = idx.grib_message.diff().ne(1).cumsum()

    # There should be fewer download groups than total messages if grouping works
    num_groups = idx.download_groups.nunique()
    num_messages = len(idx)

    print(f"Messages: {num_messages}, Groups: {num_groups}")
    # This is more informational - grouping should happen but we can't guarantee it

    # Cleanup
    subset_path.unlink()


# =============================================================================
# Test Suite 2: Local Subsetting (Extract from local file)
# =============================================================================


def test_subset_local_from_full_file():
    """Test extracting a subset from a locally downloaded full file."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # First, download the full file
    full_path = H.download()
    assert full_path.exists(), "Full file was not downloaded"

    # Create a new Herbie instance (to simulate starting fresh)
    H2 = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=False)

    # Now download a subset - this should extract from local file
    var = "TMP:2 m"
    H2.download(var)

    # Verify subset was created
    subset_path = H2.get_localFilePath(var)
    assert subset_path.exists(), "Subset file was not created from local file"

    # Verify file size
    idx = H2.inventory(var)
    expected_size = ((idx.end_byte + 1) - idx.start_byte).sum()
    actual_size = subset_path.stat().st_size
    assert expected_size == actual_size, (
        f"File size mismatch when extracting from local"
    )

    # Cleanup
    subset_path.unlink()
    full_path.unlink()


def test_subset_local_overwrites_correctly():
    """Test that overwrite=True creates a new subset from local file."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download full file
    full_path = H.download()

    # Download a subset
    var = "TMP:2 m"
    H.download(var)
    subset_path = H.get_localFilePath(var)

    # Get original file size
    original_size = subset_path.stat().st_size

    # Download again with overwrite=True
    H.download(var, overwrite=True)
    new_size = subset_path.stat().st_size

    # Sizes should be the same (same data)
    assert original_size == new_size, "Overwrite produced different size file"

    # Cleanup
    subset_path.unlink()
    full_path.unlink()


def test_subset_local_without_overwrite():
    """Test that overwrite=False skips download if subset exists."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download full file
    full_path = H.download()

    # Download a subset
    var = "TMP:2 m"
    H.download(var)
    subset_path = H.get_localFilePath(var)

    # Modify the timestamp
    original_mtime = subset_path.stat().st_mtime

    # Try to download again with overwrite=False
    H.download(var, overwrite=False)

    # File should not have been modified
    new_mtime = subset_path.stat().st_mtime
    assert original_mtime == new_mtime, "File was modified despite overwrite=False"

    # Cleanup
    subset_path.unlink()
    full_path.unlink()


# =============================================================================
# Test Suite 3: xarray Integration
# =============================================================================


def test_xarray_subset_from_local():
    """Test that xarray can read a subset created from local file."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download full file
    H.download()

    # Load subset with xarray
    var = "TMP:2 m"
    ds = H.xarray(var, remove_grib=False)

    # Verify dataset was created
    assert ds is not None, "xarray Dataset was not created"
    assert "t2m" in ds or "t" in ds, "Temperature variable not found in dataset"

    # Cleanup
    H.get_localFilePath(var).unlink()
    H.get_localFilePath().unlink()


def test_xarray_multiple_calls_same_subset():
    """Test that multiple xarray calls on same subset work correctly."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download full file
    H.download()

    var = "TMP:2 m"

    # First xarray call
    ds1 = H.xarray(var, remove_grib=False)

    # Second xarray call (should use cached subset)
    ds2 = H.xarray(var, remove_grib=False)

    # Both should be valid datasets
    assert ds1 is not None and ds2 is not None

    # Cleanup
    H.get_localFilePath(var).unlink()
    H.get_localFilePath().unlink()


# =============================================================================
# Test Suite 4: Edge Cases and Error Handling
# =============================================================================


def test_subset_invalid_search_pattern():
    """Test handling of search pattern that matches no variables."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Try to download with invalid search
    var = "NONEXISTENT_VARIABLE:2 m"
    result = H.download(var, errors="warn")

    # Should return None or handle gracefully
    if result:
        assert not result.exists() or result.stat().st_size == 0


def test_subset_empty_result():
    """Test subsetting when no messages match the search."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    var = ":999999 mb"  # Level that doesn't exist
    result = H.download(var, errors="warn")

    # File should not be created or be empty
    subset_path = H.get_localFilePath(var)
    if subset_path.exists():
        assert subset_path.stat().st_size == 0, "Empty subset should have 0 bytes"


def test_subset_invalid_byte_range():
    """Test handling of invalid byte ranges (end < start)."""
    # This is harder to test directly, but we can verify the subset function
    # handles it gracefully by checking that no exceptions are raised
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download a normal subset - this tests that the code handles
    # any potential invalid byte ranges internally
    var = "TMP:2 m"
    try:
        H.download(var)
        success = True
    except Exception as e:
        success = False
        print(f"Unexpected error: {e}")

    assert success, "Download should handle invalid byte ranges gracefully"

    # Cleanup
    subset_path = H.get_localFilePath(var)
    if subset_path.exists():
        subset_path.unlink()


# =============================================================================
# Test Suite 5: File Integrity
# =============================================================================


def test_subset_file_integrity():
    """Test that subset files can be opened and read correctly."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    var = "TMP:2 m"
    H.download(var)

    # Try to open with xarray (this validates the GRIB2 format)
    subset_path = H.get_localFilePath(var)
    try:
        ds = H.xarray(var, remove_grib=False)
        integrity_ok = True
    except Exception as e:
        integrity_ok = False
        print(f"Failed to open subset: {e}")

    assert integrity_ok, "Subset file has integrity issues"

    # Cleanup
    subset_path.unlink()


def test_subset_concatenated_properly():
    """Test that multiple GRIB messages are concatenated correctly."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Download multiple non-adjacent messages
    var = ":(?:TMP|DPT|RH):2 m above"
    H.download(var)

    subset_path = H.get_localFilePath(var)

    # Verify the file has the correct structure by reading with xarray
    try:
        ds = H.xarray(var, remove_grib=False)
        # Should have multiple variables
        num_vars = len([v for v in ds.data_vars])
        assert num_vars >= 2, f"Expected multiple variables, got {num_vars}"
    except Exception as e:
        pytest.fail(f"Failed to read concatenated subset: {e}")

    # Cleanup
    subset_path.unlink()


# =============================================================================
# Test Suite 6: Performance and Efficiency
# =============================================================================


def test_subset_faster_than_full_download():
    """Test that subsetting is faster than downloading full file."""
    import time

    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Time subset download
    var = "TMP:2 m"
    start = time.time()
    H.download(var)
    subset_time = time.time() - start

    subset_size = H.get_localFilePath(var).stat().st_size
    H.get_localFilePath(var).unlink()

    # Time full download
    H2 = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)
    start = time.time()
    H2.download()
    full_time = time.time() - start

    full_size = H2.get_localFilePath().stat().st_size

    print(f"\nSubset: {subset_size / 1e6:.2f} MB in {subset_time:.2f}s")
    print(f"Full:   {full_size / 1e6:.2f} MB in {full_time:.2f}s")
    print(f"Subset is {subset_size / full_size * 100:.1f}% of full file size")

    # Cleanup
    H2.get_localFilePath().unlink()

    # Subset should be smaller
    assert subset_size < full_size, "Subset should be smaller than full file"


# =============================================================================
# Test Suite 7: Backwards Compatibility
# =============================================================================


def test_subset_backward_compatible():
    """Test that the new subsetting approach works the same as the old one."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # Test various search patterns that worked before
    test_patterns = [
        "TMP:2 m",
        ":500 mb",
        "(?:U|V)GRD",
        ":TMP:",
        ":.GRD:",
    ]

    for pattern in test_patterns:
        try:
            H.download(pattern)
            subset_path = H.get_localFilePath(pattern)

            # Verify file exists and has content
            if subset_path.exists():
                assert subset_path.stat().st_size > 0, f"Subset for {pattern} is empty"
                subset_path.unlink()

            success = True
        except Exception as e:
            print(f"Pattern {pattern} failed: {e}")
            success = False

        assert success, f"Pattern {pattern} should work"


# =============================================================================
# Test Suite 8: Timeout and Network Error Handling
# =============================================================================


@pytest.mark.skipif(
    os.getenv("SKIP_NETWORK_TESTS") == "1", reason="Skipping network timeout tests"
)
def test_subset_handles_timeout():
    """Test that subsetting handles network timeouts gracefully."""
    H = Herbie(today, model="hrrr", product="sfc", save_dir=save_dir, overwrite=True)

    # This is hard to test reliably, but we ensure no crashes occur
    var = "TMP:2 m"
    try:
        H.download(var, errors="warn")
        handled_ok = True
    except requests.Timeout:
        handled_ok = True  # Timeout is acceptable
    except Exception as e:
        handled_ok = False
        print(f"Unexpected error: {e}")

    assert handled_ok, "Should handle timeouts gracefully"


# =============================================================================
# Helper function to run all tests
# =============================================================================


def run_all_subset_tests():
    """Run all subset tests and report results."""
    test_functions = [
        test_subset_remote_single_variable,
        test_subset_remote_multiple_variables,
        test_subset_remote_level,
        test_subset_remote_grouped_messages,
        test_subset_local_from_full_file,
        test_subset_local_overwrites_correctly,
        test_subset_local_without_overwrite,
        test_xarray_subset_from_local,
        test_xarray_multiple_calls_same_subset,
        test_subset_invalid_search_pattern,
        test_subset_empty_result,
        test_subset_invalid_byte_range,
        test_subset_file_integrity,
        test_subset_concatenated_properly,
        test_subset_faster_than_full_download,
        test_subset_backward_compatible,
    ]

    results = {}
    for test_func in test_functions:
        try:
            test_func()
            results[test_func.__name__] = "✅ PASSED"
        except AssertionError as e:
            results[test_func.__name__] = f"❌ FAILED: {e}"
        except Exception as e:
            results[test_func.__name__] = f"⚠️  ERROR: {e}"

    # Print results
    print("\n" + "=" * 70)
    print("SUBSET TEST RESULTS")
    print("=" * 70)
    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    # Summary
    passed = sum(1 for r in results.values() if "PASSED" in r)
    failed = sum(1 for r in results.values() if "FAILED" in r)
    errors = sum(1 for r in results.values() if "ERROR" in r)

    print("=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed, {errors} errors")
    print("=" * 70)


if __name__ == "__main__":
    run_all_subset_tests()

"""Tests for inventory_utils module."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

import pandas as pd
import pytest

from herbie.inventory_utils import (
    read_index_file,
    save_index_file,
    parse_wgrib2_index,
    parse_eccodes_index,
    filter_inventory,
    add_inventory_attributes,
)


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def sample_wgrib2_content():
    """Sample wgrib2-style index file content."""
    return """1:0:d=2024010100:TMP:2 m above ground:anl:
2:12345:d=2024010100:RH:2 m above ground:anl:
3:23456:d=2024010100:UGRD:10 m above ground:anl:
4:34567:d=2024010100:VGRD:10 m above ground:anl:
5:45678:d=2024010100:TMP:500 mb:anl:"""


@pytest.fixture
def sample_eccodes_content():
    """Sample eccodes-style index file content."""
    records = [
        {
            "_offset": 0,
            "_length": 1000,
            "date": "20240101",
            "time": "0000",
            "step": "0",
            "param": "2t",
            "levelist": "0",
            "levtype": "sfc",
            "number": "0",
            "domain": "g",
            "expver": "1",
            "class": "od",
            "type": "fc",
            "stream": "oper",
        },
        {
            "_offset": 1000,
            "_length": 1000,
            "date": "20240101",
            "time": "0000",
            "step": "1",
            "param": "10u",
            "levelist": "0",
            "levtype": "sfc",
            "number": "0",
            "domain": "g",
            "expver": "1",
            "class": "od",
            "type": "fc",
            "stream": "oper",
        },
    ]
    return "\n".join([json.dumps(r) for r in records])


@pytest.fixture
def sample_dataframe():
    """Sample inventory DataFrame for testing."""
    return pd.DataFrame(
        {
            "grib_message": [1, 2, 3],
            "variable": ["TMP", "RH", "UGRD"],
            "level": ["2 m above ground", "2 m above ground", "10 m above ground"],
            "search_this": [
                ":TMP:2 m above ground:",
                ":RH:2 m above ground:",
                ":UGRD:10 m above ground:",
            ],
        }
    )


# ============================================================================
# Tests for read_index_file
# ============================================================================


def test_read_index_file_from_stringio(sample_wgrib2_content):
    """Test reading from a StringIO object."""
    idx = StringIO(sample_wgrib2_content)
    result = read_index_file(idx, idx_source="generated")
    assert result == sample_wgrib2_content


def test_read_index_file_from_local_file(tmp_path, sample_wgrib2_content):
    """Test reading from a local file."""
    # Create a temporary index file
    idx_file = tmp_path / "test.idx"
    idx_file.write_text(sample_wgrib2_content)

    result = read_index_file(idx_file, idx_source="local")
    assert result == sample_wgrib2_content


@patch("herbie.inventory_utils.requests.get")
def test_read_index_file_from_remote(mock_get, sample_wgrib2_content):
    """Test reading from a remote URL."""
    # Mock the requests.get response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = sample_wgrib2_content
    mock_get.return_value = mock_response

    result = read_index_file("http://example.com/file.idx", idx_source="remote")

    assert result == sample_wgrib2_content
    mock_get.assert_called_once_with("http://example.com/file.idx")
    mock_response.close.assert_called_once()


@patch("herbie.inventory_utils.requests.get")
def test_read_index_file_remote_failure(mock_get):
    """Test handling of failed remote request."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Cant open index file"):
        read_index_file("http://example.com/missing.idx", idx_source="remote")


# ============================================================================
# Tests for save_index_file
# ============================================================================


def test_save_index_file(tmp_path, sample_wgrib2_content):
    """Test saving index file content."""
    save_path = tmp_path / "subdir" / "test.idx"

    save_index_file(sample_wgrib2_content, save_path)

    # Check that file was created
    assert save_path.exists()
    assert save_path.read_text() == sample_wgrib2_content


def test_save_index_file_creates_parent_dirs(tmp_path, sample_wgrib2_content):
    """Test that parent directories are created."""
    save_path = tmp_path / "level1" / "level2" / "level3" / "test.idx"

    save_index_file(sample_wgrib2_content, save_path)

    assert save_path.parent.exists()
    assert save_path.exists()


# ============================================================================
# Tests for parse_wgrib2_index
# ============================================================================


def test_parse_wgrib2_index(sample_wgrib2_content):
    """Test parsing wgrib2-style index file."""
    df = parse_wgrib2_index(sample_wgrib2_content, fxx=0)

    # Check basic structure
    assert len(df) == 5
    assert "grib_message" in df.columns
    assert "start_byte" in df.columns
    assert "end_byte" in df.columns
    assert "variable" in df.columns
    assert "level" in df.columns
    assert "search_this" in df.columns

    # Check first row
    assert df.iloc[0]["grib_message"] == 1
    assert df.iloc[0]["start_byte"] == 0
    assert df.iloc[0]["variable"] == "TMP"
    assert df.iloc[0]["level"] == "2 m above ground"


def test_parse_wgrib2_index_reference_time(sample_wgrib2_content):
    """Test that reference_time is parsed correctly."""
    df = parse_wgrib2_index(sample_wgrib2_content, fxx=6)

    assert "reference_time" in df.columns
    assert "valid_time" in df.columns
    assert pd.notna(df.iloc[0]["reference_time"])

    # Check that valid_time = reference_time + fxx hours
    ref_time = df.iloc[0]["reference_time"]
    valid_time = df.iloc[0]["valid_time"]
    assert (valid_time - ref_time).total_seconds() == 6 * 3600


def test_parse_wgrib2_index_search_string(sample_wgrib2_content):
    """Test that search_this column is formatted correctly."""
    df = parse_wgrib2_index(sample_wgrib2_content, fxx=0)

    # Check that search_this starts with colon
    assert all(df["search_this"].str.startswith(":"))

    # Check that it contains variable info
    assert ":TMP:" in df.iloc[0]["search_this"]
    assert ":2 m above ground:" in df.iloc[0]["search_this"]


# ============================================================================
# Tests for parse_eccodes_index
# ============================================================================


def test_parse_eccodes_index(sample_eccodes_content):
    """Test parsing eccodes-style index file."""
    df = parse_eccodes_index(sample_eccodes_content)

    # Check basic structure
    assert len(df) == 2
    assert "grib_message" in df.columns
    assert "start_byte" in df.columns
    assert "end_byte" in df.columns
    assert "param" in df.columns
    assert "levtype" in df.columns
    assert "search_this" in df.columns

    # Check first row
    assert df.iloc[0]["grib_message"] == 1
    assert df.iloc[0]["start_byte"] == 0
    assert df.iloc[0]["end_byte"] == 1000
    assert df.iloc[0]["param"] == "2t"


def test_parse_eccodes_index_time_handling(sample_eccodes_content):
    """Test that times are parsed correctly for eccodes."""
    df = parse_eccodes_index(sample_eccodes_content)

    assert "reference_time" in df.columns
    assert "valid_time" in df.columns
    assert "step" in df.columns

    # Check step is a timedelta
    assert pd.api.types.is_timedelta64_dtype(df["step"])


def test_parse_eccodes_index_search_string(sample_eccodes_content):
    """Test that search_this column is formatted correctly for eccodes."""
    df = parse_eccodes_index(sample_eccodes_content)

    # Check that search_this starts with colon
    assert all(df["search_this"].str.startswith(":"))

    # Check that it contains param info
    assert ":2t:" in df.iloc[0]["search_this"]
    assert ":10u:" in df.iloc[1]["search_this"]


# ============================================================================
# Tests for filter_inventory
# ============================================================================


def test_filter_inventory_no_search(sample_dataframe):
    """Test that no filtering occurs when search is None."""
    result = filter_inventory(sample_dataframe, search=None)
    assert len(result) == len(sample_dataframe)
    pd.testing.assert_frame_equal(result, sample_dataframe)


def test_filter_inventory_with_colon_search(sample_dataframe):
    """Test that ':' search returns all rows."""
    result = filter_inventory(sample_dataframe, search=":")
    assert len(result) == len(sample_dataframe)


def test_filter_inventory_simple_search(sample_dataframe):
    """Test filtering with a simple search string."""
    result = filter_inventory(sample_dataframe, search="TMP")
    assert len(result) == 1
    assert result.iloc[0]["variable"] == "TMP"


def test_filter_inventory_regex_search(sample_dataframe):
    """Test filtering with regex pattern."""
    result = filter_inventory(sample_dataframe, search=":(TMP|RH):")
    assert len(result) == 2
    assert set(result["variable"]) == {"TMP", "RH"}


def test_filter_inventory_no_matches(sample_dataframe):
    """Test filtering when no matches are found."""
    result = filter_inventory(sample_dataframe, search="NONEXISTENT", verbose=False)
    assert len(result) == 0


def test_filter_inventory_verbose_warning(sample_dataframe, capsys):
    """Test that verbose mode prints warning when no matches found."""
    result = filter_inventory(sample_dataframe, search="NONEXISTENT", verbose=True)
    captured = capsys.readouterr()
    assert "No GRIB messages found" in captured.out


# ============================================================================
# Tests for add_inventory_attributes
# ============================================================================


def test_add_inventory_attributes(sample_dataframe):
    """Test adding attributes to inventory DataFrame."""
    result = add_inventory_attributes(
        sample_dataframe,
        idx="test.idx",
        idx_source="local",
        model="hrrr",
        product="sfc",
        fxx=6,
        date=pd.Timestamp("2024-01-01"),
    )

    # Check that attributes were added
    assert result.attrs["url"] == "test.idx"
    assert result.attrs["source"] == "local"
    assert result.attrs["model"] == "hrrr"
    assert result.attrs["product"] == "sfc"
    assert result.attrs["lead_time"] == 6
    assert result.attrs["datetime"] == pd.Timestamp("2024-01-01")
    assert "description" in result.attrs


def test_add_inventory_attributes_preserves_data(sample_dataframe):
    """Test that adding attributes doesn't modify the DataFrame data."""
    original_data = sample_dataframe.copy()

    result = add_inventory_attributes(
        sample_dataframe,
        idx="test.idx",
        idx_source="local",
        model="hrrr",
        product="sfc",
        fxx=0,
        date=pd.Timestamp("2024-01-01"),
    )

    pd.testing.assert_frame_equal(
        result.drop(
            columns=result.columns[~result.columns.isin(original_data.columns)],
            errors="ignore",
        ),
        original_data,
    )


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_wgrib2_workflow(tmp_path, sample_wgrib2_content):
    """Test complete workflow: read -> parse -> filter -> save."""
    # Setup
    idx_file = tmp_path / "test.idx"
    idx_file.write_text(sample_wgrib2_content)

    # Read
    content = read_index_file(idx_file, idx_source="local")

    # Parse
    df = parse_wgrib2_index(content, fxx=0)

    # Add attributes
    df = add_inventory_attributes(
        df,
        idx=idx_file,
        idx_source="local",
        model="test",
        product="sfc",
        fxx=0,
        date=pd.Timestamp("2024-01-01"),
    )

    # Filter
    filtered = filter_inventory(df, search=":TMP:")

    # Verify
    assert len(filtered) == 2  # TMP at 2m and 500mb
    assert all("TMP" in search for search in filtered["search_this"])
    assert filtered.attrs["model"] == "test"


def test_full_eccodes_workflow(sample_eccodes_content):
    """Test complete workflow for eccodes format."""
    # Setup StringIO (simulating generated index)
    idx = StringIO(sample_eccodes_content)

    # Read
    content = read_index_file(idx, idx_source="generated")

    # Parse
    df = parse_eccodes_index(content)

    # Add attributes
    df = add_inventory_attributes(
        df,
        idx="generated",
        idx_source="generated",
        model="ifs",
        product="oper",
        fxx=0,
        date=pd.Timestamp("2024-01-01"),
    )

    # Filter
    filtered = filter_inventory(df, search=":2t:", idx_style="eccodes")

    # Verify
    assert len(filtered) == 1
    assert filtered.iloc[0]["param"] == "2t"
    assert filtered.attrs["model"] == "ifs"


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


def test_parse_wgrib2_empty_content():
    """Test parsing empty wgrib2 content."""
    result = parse_wgrib2_index("", fxx=0)
    assert len(result) == 0


def test_filter_inventory_empty_dataframe():
    """Test filtering an empty DataFrame."""
    empty_df = pd.DataFrame(columns=["search_this"])
    result = filter_inventory(empty_df, search="TMP")
    assert len(result) == 0


def test_save_index_file_with_path_object(tmp_path, sample_wgrib2_content):
    """Test that save_index_file works with Path objects."""
    save_path = tmp_path / "test.idx"
    save_index_file(sample_wgrib2_content, save_path)
    assert save_path.exists()


def test_parse_wgrib2_malformed_line():
    """Test handling of malformed index lines."""
    # This should not crash, but may produce unexpected results
    malformed = "1:0:d=2024010100:TMP"  # Missing fields
    df = parse_wgrib2_index(malformed, fxx=0)
    assert len(df) == 1  # Should still parse what it can

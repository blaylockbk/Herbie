import pytest
from datetime import datetime
from herbie.toolbox import str_to_datetime


def test_valid_iso_format():
    """Test parsing of ISO 8601 format."""
    assert str_to_datetime("2025-01-26T14:30:45") == datetime(2025, 1, 26, 14, 30, 45)


def test_valid_compact_format():
    """Test parsing of compact date-time format."""
    assert str_to_datetime("20250126143045") == datetime(2025, 1, 26, 14, 30, 45)


def test_valid_slash_separated_format():
    """Test parsing of slash-separated format."""
    assert str_to_datetime("2025/01/26 14:30") == datetime(2025, 1, 26, 14, 30)


def test_missing_time():
    """Test parsing of a string with only the date."""
    assert str_to_datetime("2025-01-26") == datetime(2025, 1, 26, 0, 0, 0)


def test_invalid_format():
    """Test handling of an invalid format."""
    with pytest.raises(
        ValueError, match=r"does not match the expected date-time format"
    ):
        str_to_datetime("invalid-string")


def test_invalid_date():
    """Test handling of an invalid date."""
    with pytest.raises(ValueError, match=r"Invalid date-time components extracted"):
        str_to_datetime("2025-02-30T12:00:00")


def test_missing_components():
    """Test handling of missing components in the input."""
    with pytest.raises(
        ValueError, match=r"does not match the expected date-time format"
    ):
        str_to_datetime("2025")

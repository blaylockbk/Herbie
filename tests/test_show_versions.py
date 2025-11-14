"""Test show_versions function."""

import herbie


def test_show_versions(capsys):
    """Test that show_versions prints expected sections."""
    herbie.show_versions()

    captured = capsys.readouterr()
    output = captured.out

    # Check that key sections are present
    assert "OPERATING SYSTEM" in output
    assert "PYTHON VERSION" in output
    assert "HERBIE VERSION" in output
    assert "CORE DEPENDENCIES" in output

    # Check a few specific packages
    assert "pandas" in output
    assert "xarray" in output
    assert "requests" in output

    # Check for executables even if not installed
    assert "curl" in output
    assert "wgrib2" in output

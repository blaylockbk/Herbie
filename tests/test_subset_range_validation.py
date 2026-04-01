"""Test that subset downloads validate HTTP Range request responses."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from herbie import Herbie, config

now = datetime.now()
today = datetime(now.year, now.month, now.day, now.hour) - timedelta(hours=6)

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


def test_subset_raises_on_non_206_response():
    """RuntimeError should fire when the server returns 200 instead of 206.

    This prevents the silent disk-space blowup described in issue #514:
    without the guard, each subset group downloads the entire multi-GB
    file and appends it, producing output many times larger than the
    source.
    """
    H = Herbie(
        today,
        model="hrrr",
        product="sfc",
        save_dir=save_dir,
        overwrite=True,
    )

    # Force the index to be fetched and cached before we patch requests.
    _ = H.index_as_dataframe

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": "9999999999"}
    mock_response.raise_for_status = Mock()
    mock_response.close = Mock()

    with patch("herbie.core.requests.get", return_value=mock_response):
        with pytest.raises(RuntimeError, match="Range request not honored"):
            H.download("TMP:2 m", overwrite=True)

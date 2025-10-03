"""
Simple, parametrized download tests for the RTMA family using ~6 hours ago.

Domains covered:
- rtma, rtma_ru, rtma_hi, rtma_pr, rtma_gu, rtma_ak

We download a very small subset (TMP at 2 m AGL) to keep the test fast.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from herbie import Herbie, config

# Use ~6 hours ago (rounded to the hour) to avoid edge cases at the current cycle.
six_hours_ago = (
    datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    - timedelta(hours=6)
).replace(tzinfo=None)   # strip tz to make it naive

SAVE_DIR = config["default"]["save_dir"] / "Herbie-Tests-Data" / "rtma-family"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Small GRIB2 filter to keep download size down
FILTER = ":TMP:2 m above ground:"

MODELS = ["rtma", "rtma_ru", "rtma_hi", "rtma_pr", "rtma_gu", "rtma_ak"]


@pytest.mark.parametrize("model_name", MODELS)
def test_rtma_family_download_6h_ago(model_name):
    """
    Download a minimal field for each RTMA domain at ~6 hours ago.
    """
    H = Herbie(
        six_hours_ago,
        model=model_name,
        product="anl",
        save_dir=SAVE_DIR,
        overwrite=True,
    )
    f = H.download(FILTER)

    local = H.get_localFilePath(FILTER)
    assert local.exists(), f"Expected file for {model_name} at {six_hours_ago}"

    # Clean up to keep caches small
    try:
        Path(local).unlink(missing_ok=True)
    except Exception:
        pass

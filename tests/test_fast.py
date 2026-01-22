"""Tests FastHerbie."""

from herbie import FastHerbie, config
import pandas as pd
import pytest

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

# Remove all previous test data
for i in (save_dir / "hrrr").rglob("*"):
    if i.is_file():
        i.unlink()


@pytest.mark.parametrize("model", ["hrrr", "gfs", "gefs"])
def test_FastHerbie(model):
    DATES = pd.date_range("2022-01-01", "2022-01-01 02:00", freq="1h")
    DATA_VARS = {
        "hrrr": "TMP:2 m",
        "gfs": "TMP:2 m",
        "gefs": "TMP:2 m",
    }
    KWARGS = {
        "hrrr": {},
        "gfs": {},
        "gefs": {
            "member": "avg",
            "product": "atmos.5",
        },
    }

    # Create Fast Herbie
    FH = FastHerbie(
        DATES, fxx=range(0, 3), save_dir=save_dir, model=model, **KWARGS[model]
    )

    assert len(FH) == 9

    # Download subset of these files
    FH.download(DATA_VARS[model])

    # Load these files
    FH.xarray(DATA_VARS[model])

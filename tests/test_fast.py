"""Tests FastHerbie."""

from herbie import FastHerbie, config
import pandas as pd

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"

# Remove all previous test data
for i in (save_dir / "hrrr").rglob("*"):
    if i.is_file():
        i.unlink()


def test_FastHerbie():
    DATES = pd.date_range("2022-01-01", "2022-01-01 02:00", freq="1h")

    # Create Fast Herbie
    FH = FastHerbie(
        DATES,
        fxx=range(0, 3),
        save_dir=save_dir,
    )
    assert len(FH) == 9

    # Download subset of these files
    FH.download("TMP:2 m")

    # Load these files
    FH.xarray("TMP:2 m")
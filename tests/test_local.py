"""Test using local directory for data files."""

from herbie import Herbie, config
import pytest

DATA_DIRECTORY = config["default"]["save_dir"] / "Herbie-Tests-Data/"
HERBIE_OPTIONS = {
    "verbose": True,
    "overwrite": False,
    "save_dir": DATA_DIRECTORY,
}

@pytest.fixture
def setup_local_data(request):
    date, model, product = request.param    
    H = Herbie(date, 
        model=model, 
        product=product,
        **HERBIE_OPTIONS
    )

    print(f"{H.save_dir=}")

    H.download(verbose=True)
    print(f"{H.idx_source=}")

    print(H.inventory())
    return date, model, product


@pytest.mark.parametrize(
    "setup_local_data",
    [
        ("2025-08-08", "gfs", "pgrb2.0p25"),
        ("2020-10-27", "gfs", "0.5-degree"),
        ("2025-08-10", "hrrr", "sfc"),
        ("2025-08-01", "rap", "awp200"),
        ("2025-08-05", "ifs", "wave"),
    ],
    indirect=True,
    ids=[
        "gfs-2025-08-08", 
        "gfs-2020-10-27",
        "hrrr-2025-08-10",
        "rap-2025-08-01",
        "ifs-2025-08-05",
    ],
)
def test_local_data(setup_local_data):
    date, model, product = setup_local_data
    H = Herbie(date, 
        model=model, 
        product=product,
        **HERBIE_OPTIONS
    )

    assert "local" == H.idx_source
    assert "local" == H.grib_source

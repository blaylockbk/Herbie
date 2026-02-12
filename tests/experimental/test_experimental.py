from herbie.experimental import Herbie


def test_basic_gfs():
    H = Herbie("2025-12-10", model="gfs", resolution=1.0, product="uncommon")


def test_basic_hrrr():
    H = Herbie("2025-12-10", model="hrrr", product="surface")


def test_basic_ifs():
    H = Herbie("2025-12-10", model="ifs")


def test_basic_rtma():
    H = Herbie("2025-12-10", model="rtma")

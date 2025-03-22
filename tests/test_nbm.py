from herbie import Herbie, config

save_dir = config["default"]["save_dir"] / "Herbie-Tests-Data/"


class TestNBM:
    """Tests for National Blend of Models."""

    def test_nbm(self):
        """Test creating a Herbie object for NBM."""
        H = Herbie(
            "2025-03-04 12:00",
            model="nbm",
            product="co",
            fxx=1,
            save_dir=save_dir,
        )
        assert H.grib
        assert H.idx

        H.xarray(":TMP:2 m above ground:1 hour fcst:")

    def test_nbqmd(self):
        """Test creating a Herbie object for NBMQMD."""
        H = Herbie(
            "2025-03-04 12:00",
            model="nbmqmd",
            product="co",
            fxx=1,
            save_dir=save_dir,
        )
        assert H.grib
        assert H.idx

        H.xarray(":APCP:")

"""Tests for reading index files into inventory DataFrame."""

from herbie.inventory import read_wgrib2_index, read_eccodes_index


def test_read_wgrib2_index_hrrr():
    """Test reading wgrib2 index files."""
    df_local = read_wgrib2_index(
        "./sample_data/index_files/hrrr.t00z.wrfsfcf00.grib2.idx"
    )
    df_remote = read_wgrib2_index(
        "https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20231201/conus/hrrr.t00z.wrfsfcf00.grib2.idx"
    )

    assert df_local.equals(df_remote)


def test_read_wgrib2_index_rap():
    """Test reading wgrib2 index files."""
    df_local = read_wgrib2_index(
        "./sample_data/index_files/rap.t00z.awp130pgrbf00.grib2.idx"
    )
    df_remote = read_wgrib2_index(
        "https://noaa-rap-pds.s3.amazonaws.com/rap.20231201/rap.t00z.awp130pgrbf00.grib2.idx"
    )

    assert df_local.equals(df_remote)


def test_read_eccodes_index_ecmwf():
    """Test reading wgrib2 index files."""
    df_local = read_eccodes_index("./sample_data/index_files/20231201000000-0h-oper-fc.index")
    df_remote = read_eccodes_index("https://ai4edataeuwest.blob.core.windows.net/ecmwf/20231201/00z/0p4-beta/oper/20231201000000-0h-oper-fc.index")

    assert df_local.equals(df_remote)

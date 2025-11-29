if __name__ == "__main__":
    import polars as pl

    from herbie import Herbie
    from herbie.experimental.download import download_grib2_from_dataframe
    from herbie.experimental.inventory import create_download_groups, _read_wgrib2_index

    H = Herbie("2025-11-01", model="hrrr")
    df = _read_wgrib2_index(H.idx)

    df = df.filter(
        pl.col("variable").is_in(["UGRD", "VGRD", "TMP"]),
    )

    df = create_download_groups(df)

    # Download the GRIB2 data
    download_grib2_from_dataframe(
        df=df,
        output_file="output.grib2",
        max_workers=5,
    )

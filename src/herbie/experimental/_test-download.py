if __name__ == "__main__":
    import logging

    import polars as pl

    from herbie import Herbie
    from herbie.experimental.download import download_grib2_from_dataframe
    from herbie.experimental.inventory import read_index_file, create_download_groups

    logging.getLogger("herbie.core").setLevel("DEBUG")
    logging.getLogger("herbie.experimental.downloader").setLevel("DEBUG")
    logging.getLogger("herbie.experimental.inventory").setLevel("DEBUG")

    model = "ifs"

    H = Herbie("2025-11-01", model="ifs")
    df = read_index_file(H.idx)

    if model != "ifs":
        df = df.filter(
            pl.col("variable").is_in(["UGRD", "VGRD", "TMP"]),
        )
    else:
        df = df.filter(
            pl.col("param").is_in(["t", "u", "v"]),
        )

    df = create_download_groups(df)

    # Download the GRIB2 data
    download_grib2_from_dataframe(
        df=df,
        output_file="output.grib2",
        max_workers=5,
    )

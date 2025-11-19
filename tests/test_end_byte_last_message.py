"""Test handling of last-message end_byte when indexing wgrib2-style files."""

from pathlib import Path

from herbie import Herbie


def test_end_byte_for_last_message_dummy(tmp_path):
    """Test last grib message end byte range.

    If the requested grid is the last message, the subset should
    be written using the file's final byte as the end of the range.

    In response to:
    https://github.com/blaylockbk/Herbie/issues/496
    """
    # Create a small dummy GRIB-like file (300 bytes)
    grib_path = tmp_path / "test.grib2"
    grib_path.write_bytes(b"\x00" * 300)

    # Create a simple wgrib2-style index with two messages. The
    # second message starts at byte 200 and is intentionally the
    # last message in the file (its end_byte would otherwise be NaN).
    idx_path = tmp_path / "test.grib2.idx"
    lines = [
        # grib_message:start_byte:reference_time:variable:level:forecast_time:?:??:???
        "1:0:d=2025111300:TMP:2 m:0 hour:region:extra:more",
        "2:200:d=2025111300:PRMSL:msl:0 hour:region:extra:more",
    ]
    idx_path.write_text("\n".join(lines) + "\n")

    # Construct a Herbie instance and point it at our local files. Use a
    # small save_dir under tmp_path so output is written there.
    H = Herbie(
        "2025-11-13 00:00",
        model="gefs",
        member="c00",
        product="atmos.5",
        fxx=24,
        save_dir=tmp_path,
        overwrite=True,
        verbose=False,
    )

    # Force Herbie to use our local files and treat them as local sources
    H.grib = str(grib_path)
    H.idx = str(idx_path)
    H.idx_source = "local"
    H.grib_source = "local"
    H.IDX_STYLE = "wgrib2"

    # Ensure the output directory exists (get_localFilePath will return the path)
    out_file = H.get_localFilePath(":PRMSL:")
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Run the download subset for the last-message variable and verify
    # that the resulting subset file exists and has the expected length
    # (from byte 200 to 299 -> 100 bytes).
    result = H.download(":PRMSL:")
    assert Path(result).exists()
    assert Path(result).stat().st_size == 100


def test_end_byte_for_last_message_real(tmp_path):
    """Test subset last grib message.

    In response to:
    https://github.com/blaylockbk/Herbie/issues/496
    """
    # Construct a Herbie instance and point it at our local files. Use a
    # small save_dir under tmp_path so output is written there.
    H = Herbie(
        "2025-11-13 00:00",
        model="gefs",
        member="c00",
        product="atmos.5",
        fxx=24,
        save_dir=tmp_path,
        overwrite=True,
        verbose=False,
    )

    # Get last grib message
    last_msg = H.inventory().iloc[-1]["search_this"]

    assert len(H.inventory(last_msg)) == 1

    # Download last grib message
    f = H.download(last_msg, overwrite=True)
    assert f.exists()

    # Read with xarray
    ds = H.xarray(last_msg, overwrite=True)
    assert len(ds) == 1

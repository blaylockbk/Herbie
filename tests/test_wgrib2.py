"""Tests for the wgrib2 wrapper that do not need wgrib2 or a network."""

import os
import stat
import sys

import pytest

from herbie.wgrib2 import wgrib2

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="uses a POSIX shell script as a stand-in for wgrib2"
)


@pytest.fixture
def fake_wgrib2(tmp_path, monkeypatch):
    """Replace wgrib2 with a script that prints one argument per line.

    For ``-small_grib`` it also creates the output file, as wgrib2 does.
    """
    exe = tmp_path / "bin" / "wgrib2"
    exe.parent.mkdir()
    exe.write_text(
        "#!/bin/sh\n"
        'if [ "$2" = "-small_grib" ]; then : > "$5"; fi\n'
        'for a in "$@"; do printf "%s\\n" "$a"; done\n'
    )
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(wgrib2, "wgrib2", str(exe))
    return exe


def test_inventory_does_not_run_a_shell(fake_wgrib2, tmp_path):
    """A file path is one argument to wgrib2, never shell syntax (#561)."""
    marker = tmp_path / "pwned"
    FILE = tmp_path / f"x.grib2; touch {marker}"

    out = wgrib2.inventory(FILE)

    assert out.splitlines() == ["-s", str(FILE)]
    assert not marker.exists()


def test_region_name_does_not_run_a_shell(fake_wgrib2, tmp_path, monkeypatch):
    """The region name and file path are passed as arguments (#561)."""
    # The name becomes part of a file name, so it cannot hold "/".
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "pwned_region"
    grib = tmp_path / "in.grib2"
    grib.write_bytes(b"")
    name = "z; touch pwned_region; "

    outfile = wgrib2.region(grib, (0, 1, 2, 3), name=name)

    assert outfile == tmp_path / f"{name}_in.grib2"
    assert not marker.exists()


def test_create_inventory_file_with_hostile_filename(
    fake_wgrib2, tmp_path, monkeypatch
):
    """A file name found in a directory is not run as a command (#561)."""
    # A file name cannot hold "/", so the planted command writes to the cwd.
    monkeypatch.chdir(tmp_path)
    marker = tmp_path / "pwned_filename"
    data = tmp_path / "data"
    data.mkdir()
    grib = data / "a;touch pwned_filename;b.grib2"
    grib.write_bytes(b"")

    idx = wgrib2.create_inventory_file(data)

    assert idx == data / f"{grib.name}.idx"
    assert idx.read_text().splitlines() == ["-s", str(grib)]
    assert not marker.exists()


def test_missing_wgrib2(monkeypatch, tmp_path):
    """Without wgrib2 on PATH the wrapper says so instead of running anything."""
    monkeypatch.setattr(wgrib2, "wgrib2", None)
    marker = tmp_path / "pwned"
    with pytest.raises(FileNotFoundError, match="wgrib2"):
        wgrib2.inventory(f"x.grib2; touch {marker}")
    assert not marker.exists()
    assert os.listdir(tmp_path) == []

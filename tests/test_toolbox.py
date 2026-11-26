import sys
from types import SimpleNamespace
from typing import cast

import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
import pandas as pd
import pytest
import xarray as xr

from herbie.toolbox import EasyMap, pc
from herbie.toolbox.cartopy_tools import EasyMapTheme, _normalize_extent


def test_EasyMap():
    map_ = EasyMap()
    assert map_.ax is not None
    assert map_.STATES().ax is not None


def test_EasyMap_does_not_create_regular_axes_on_empty_figure():
    fig = plt.figure()
    try:
        map_ = EasyMap(add_coastlines=False)
        assert fig.axes == [map_.ax]
        assert map_.ax.get_xlim() == (-180, 180)
        assert map_.ax.get_ylim() == (-90, 90)
    finally:
        plt.close(fig)


def test_EasyMap_scatterplot_narwhals_dataframe(monkeypatch):
    calls = {}
    native_calls = {}

    def fake_scatterplot(**kwargs):
        calls.update(kwargs)
        return kwargs["ax"]

    pandas_df = pd.DataFrame({"longitude": [-110], "latitude": [40], "type": ["A"]})
    native_df = object()

    def fake_from_native(data):
        native_calls["data"] = data
        return SimpleNamespace(to_pandas=lambda: pandas_df)

    monkeypatch.setitem(
        sys.modules, "narwhals", SimpleNamespace(from_native=fake_from_native)
    )
    monkeypatch.setitem(
        sys.modules, "seaborn", SimpleNamespace(scatterplot=fake_scatterplot)
    )

    ax = EasyMap(add_coastlines=False).ax

    result = ax.scatterplot(native_df, hue="type", style="type")

    assert result is ax
    assert native_calls["data"] is native_df
    assert calls["data"] is pandas_df
    assert calls["x"] == "longitude"
    assert calls["y"] == "latitude"
    assert calls["hue"] == "type"
    assert calls["style"] == "type"
    assert calls["transform"] is pc
    assert calls["ax"] is ax


def test_EasyMap_scatterplot_pandas(monkeypatch):
    calls = {}

    def fake_scatterplot(**kwargs):
        calls.update(kwargs)
        return kwargs["ax"]

    df = pd.DataFrame({"lon": [-110], "lat": [40]})
    monkeypatch.setitem(
        sys.modules,
        "narwhals",
        SimpleNamespace(from_native=lambda data: SimpleNamespace(to_pandas=lambda: df)),
    )
    monkeypatch.setitem(
        sys.modules, "seaborn", SimpleNamespace(scatterplot=fake_scatterplot)
    )
    map_ = EasyMap(add_coastlines=False)
    ax = map_.ax

    result = map_.scatterplot(df, x="lon", y="lat")

    assert result is ax
    assert calls["data"] is df
    assert calls["x"] == "lon"
    assert calls["y"] == "lat"


def test_EasyMap_rejects_unknown_theme():
    """Reject invalid themes with a helpful list of accepted choices."""
    with pytest.raises(ValueError, match="Unknown theme 'not-a-theme'"):
        EasyMap(theme=cast(EasyMapTheme, "not-a-theme"))


def test_EasyMap_mario_theme_uses_green_lakes_and_rivers():
    fig = plt.figure()
    try:
        map_ = EasyMap(theme="mario", add_coastlines=False).LAKES().RIVERS()
        lake, river = map_.ax.collections

        assert tuple(lake.get_facecolor()[0]) == to_rgba("#00A800")
        assert tuple(river.get_edgecolor()[0]) == to_rgba("#00A800")
        assert river.get_facecolor().size == 0
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    "theme",
    ["print", "high_contrast", "ocean", "mono", "retro", "night", "candy"],
)
def test_EasyMap_accepts_additional_themes(theme):
    fig = plt.figure()
    try:
        map_ = EasyMap(theme=theme, add_coastlines=False)
        assert map_.theme == theme
        assert map_.theme_dict["land"]
        assert map_.theme_dict["water"]
    finally:
        plt.close(fig)


def test_EasyMap_center_extent_requires_location():
    """Require coordinates or a named location when centering a map."""
    map_ = EasyMap(add_coastlines=False)

    with pytest.raises(ValueError, match="Provide both lon and lat"):
        map_.center_extent()


def test_EasyMap_adjust_extent_does_not_mutate_padding():
    """Keep caller-owned padding options unchanged."""
    map_ = EasyMap(add_coastlines=False)
    padding = {}

    map_.adjust_extent(pad=padding)

    assert padding == {}


def test_EasyMap_rejects_invalid_figsize():
    """Require two dimensions when figsize is a sequence."""
    with pytest.raises(ValueError, match="sequence of two values"):
        EasyMap(figsize=(8,), add_coastlines=False)


def test_EasyMap_extent_accepts_xarray_coordinates():
    """Normalize documented latitude/longitude coordinates."""
    data = xr.Dataset(coords={"longitude": [100, 110], "latitude": [30, 40]})

    assert _normalize_extent(data) == (100, 110, 30, 40)


def test_EasyMap_extent_rejects_missing_coordinates():
    """Explain which coordinates are required for an xarray extent."""
    data = xr.Dataset(coords={"time": [0]})

    with pytest.raises(ValueError, match="longitude/latitude or lon/lat"):
        _normalize_extent(data)


def test_EasyMap_scatterplot_narwhals_rejects_unsupported_data(monkeypatch):
    def unsupported_data(data):
        raise TypeError("Unsupported dataframe type")

    monkeypatch.setitem(
        sys.modules, "narwhals", SimpleNamespace(from_native=unsupported_data)
    )
    monkeypatch.setitem(
        sys.modules, "seaborn", SimpleNamespace(scatterplot=lambda **kwargs: None)
    )
    ax = EasyMap(add_coastlines=False).ax

    with pytest.raises(TypeError, match="Unsupported dataframe type"):
        ax.scatterplot({"longitude": [-110], "latitude": [40]})

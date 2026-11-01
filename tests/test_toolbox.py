import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from herbie.toolbox import EasyMap, pc, ccrs


def test_EasyMap():
    ax = EasyMap().ax
    ax = EasyMap().STATES().ax


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
    ax = EasyMap(add_coastlines=False).ax

    result = ax.scatterplot(df, x="lon", y="lat")

    assert result is ax
    assert calls["data"] is df
    assert calls["x"] == "lon"
    assert calls["y"] == "lat"


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

"""
Herbie v2 — lazy, source-agnostic access to gridded weather model output.

Quick start
-----------
>>> from herbie.v2 import Herbie, HRRR, GFS, IFS

>>> # Namespace style
>>> H = Herbie.HRRR("2025-01-01", fxx=6, product="sfc")

>>> # Direct style (equivalent)
>>> H = HRRR("2025-01-01", fxx=6, product="sfc")

>>> # Inspect available fields
>>> H.inventory("TMP:2 m above ground")

>>> # Download a subset
>>> H.download("TMP:2 m above ground")

>>> # Open as xarray
>>> ds = H.xarray("TMP:2 m above ground")

>>> # Check all remote sources and local files
>>> H.status()
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import herbie.v2.models as _models_pkg
from herbie.v2._base import HerbieModel
from herbie.v2._namespace import Herbie
from herbie.v2.fast import FastHerbie

# ---------------------------------------------------------------------------
# Auto-discover and register all HerbieModel subclasses
# ---------------------------------------------------------------------------

_registered: dict[str, type[HerbieModel]] = {}

for _finder, _module_name, _is_pkg in pkgutil.iter_modules(_models_pkg.__path__):
    if _module_name.startswith("_"):
        continue

    _mod = importlib.import_module(f"herbie.v2.models.{_module_name}")

    for _cls_name, _cls in inspect.getmembers(_mod, inspect.isclass):
        if (
            issubclass(_cls, HerbieModel)
            and _cls is not HerbieModel
            and _cls.__module__ == _mod.__name__
        ):
            # Attach to the Herbie namespace class
            setattr(Herbie, _cls_name, _cls)

            # Also export at module level so `from herbie.v2 import HRRR` works
            globals()[_cls_name] = _cls

            _registered[_cls_name] = _cls

# ---------------------------------------------------------------------------
# Plugin support via entry points
# ---------------------------------------------------------------------------
# Third-party packages can register custom model classes by declaring an
# entry point in their pyproject.toml:
#
#   [project.entry-points."herbie.v2.models"]
#   MyModel = "mypkg.models:MyModel"
#
# The class must subclass HerbieModel.

try:
    from importlib.metadata import entry_points as _entry_points

    for _ep in _entry_points(group="herbie.v2.models"):
        _cls = _ep.load()
        if isinstance(_cls, type) and issubclass(_cls, HerbieModel):
            setattr(Herbie, _cls.__name__, _cls)
            globals()[_cls.__name__] = _cls
            _registered[_cls.__name__] = _cls
except Exception:
    pass

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["Herbie", "HerbieModel", "FastHerbie"] + list(_registered.keys())

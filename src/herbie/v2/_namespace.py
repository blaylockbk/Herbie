"""
Herbie namespace class.

``herbie.v2.__init__`` discovers all ``HerbieModel`` subclasses in the
``models/`` package and attaches them as class attributes of ``Herbie``.

This gives users three equivalent calling styles::

    from herbie.v2 import Herbie
    H = Herbie.HRRR("2025-01-01", step=6)   # namespace style

    from herbie.v2 import HRRR
    H = HRRR("2025-01-01", step=6)           # direct style

    import herbie.v2 as herbie
    H = herbie.HRRR("2025-01-01", step=6)   # module attribute style

IDE / type-checker support
--------------------------
The ``TYPE_CHECKING`` block below declares all built-in model classes as
class-level attributes.  At runtime these lines are never executed (so
there is no import overhead and no circular-import risk), but Pylance,
pyright, mypy, and any other static analyser will see them and provide
full autocomplete, hover documentation, and parameter hints.

Third-party models registered via the ``herbie.v2.models`` entry-point
group will not appear here, but they can add their own stubs in the same
way by patching ``Herbie`` inside a ``TYPE_CHECKING`` block in their own
package.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    # ── NOAA convection-allowing / mesoscale ──────────────────────────────
    from herbie.v2.models.hrrr import HRRR, HRRRAK

    # ── NOAA global ───────────────────────────────────────────────────────
    from herbie.v2.models.gfs import GFS, GDAS, GFSWave

    # ── NOAA regional / analysis ──────────────────────────────────────────
    from herbie.v2.models.noaa_models import GEFS, NAM, NBM, RRFS
    from herbie.v2.models.rap import RAP, RAPHistorical
    from herbie.v2.models.rtma import RTMA, RTMA_AK, URMA

    # ── NOAA ensemble / specialty ─────────────────────────────────────────
    from herbie.v2.models.more_models import AIGFS, CFS, HGEFS, HREF, NBMQMD

    # ── Hurricane / Navy ──────────────────────────────────────────────────
    from herbie.v2.models.hurricane_and_navy import (
        HAFSA,
        HAFSB,
        HIRESW,
        NavgemGODAE,
        NavgemNOMADS,
    )

    # ── ECMWF ─────────────────────────────────────────────────────────────
    from herbie.v2.models.ecmwf import AIFS, IFS

    # ── Canadian MSC ──────────────────────────────────────────────────────
    from herbie.v2.models.canada import GDPS, HRDPS, RDPS


class Herbie:
    """
    Namespace for Herbie v2 model classes.

    Available models are attached as class attributes at import time::

        Herbie.HRRR    — High-Resolution Rapid Refresh (CONUS)
        Herbie.HRRRAK  — High-Resolution Rapid Refresh (Alaska)
        Herbie.GFS     — Global Forecast System
        Herbie.GDAS    — Global Data Assimilation System
        Herbie.GFSWave — GFS Wave Products
        Herbie.IFS     — ECMWF Integrated Forecast System
        Herbie.AIFS    — ECMWF AI Integrated Forecast System
        Herbie.RAP     — Rapid Refresh
        Herbie.RAPHistorical — RAP/RUC historical archive
        Herbie.RTMA    — Real-Time Mesoscale Analysis (CONUS)
        Herbie.RTMA_AK — Real-Time Mesoscale Analysis (Alaska)
        Herbie.URMA    — Un-Restricted Mesoscale Analysis
        Herbie.NAM     — North America Mesoscale
        Herbie.NBM     — National Blend of Models
        Herbie.GEFS    — Global Ensemble Forecast System
        Herbie.RRFS    — Rapid Refresh Forecast System

    Each model class can also be imported directly::

        from herbie.v2 import HRRR
        H = HRRR("2025-01-01", step=6)
    """

    # ── Static type annotations for IDE support ───────────────────────────
    # These are only evaluated by type checkers (TYPE_CHECKING=True); at
    # runtime __init__.py populates these via setattr().  Keeping them here
    # means Pylance / pyright / mypy resolve the full class signature and
    # surface docstrings, parameter hints, and autocomplete for all methods.

    if TYPE_CHECKING:
        # NOAA convection-allowing / mesoscale
        HRRR: ClassVar[type[HRRR]]
        HRRRAK: ClassVar[type[HRRRAK]]

        # NOAA global
        GFS: ClassVar[type[GFS]]
        GDAS: ClassVar[type[GDAS]]
        GFSWave: ClassVar[type[GFSWave]]

        # NOAA regional / analysis
        NAM: ClassVar[type[NAM]]
        NBM: ClassVar[type[NBM]]
        GEFS: ClassVar[type[GEFS]]
        RRFS: ClassVar[type[RRFS]]
        RAP: ClassVar[type[RAP]]
        RAPHistorical: ClassVar[type[RAPHistorical]]
        RTMA: ClassVar[type[RTMA]]
        RTMA_AK: ClassVar[type[RTMA_AK]]
        URMA: ClassVar[type[URMA]]

        # NOAA ensemble / specialty
        AIGFS: ClassVar[type[AIGFS]]
        CFS: ClassVar[type[CFS]]
        HGEFS: ClassVar[type[HGEFS]]
        HREF: ClassVar[type[HREF]]
        NBMQMD: ClassVar[type[NBMQMD]]

        # Hurricane / Navy
        HAFSA: ClassVar[type[HAFSA]]
        HAFSB: ClassVar[type[HAFSB]]
        HIRESW: ClassVar[type[HIRESW]]
        NavgemNOMADS: ClassVar[type[NavgemNOMADS]]
        NavgemGODAE: ClassVar[type[NavgemGODAE]]

        # ECMWF
        IFS: ClassVar[type[IFS]]
        AIFS: ClassVar[type[AIFS]]

        # Canadian MSC
        HRDPS: ClassVar[type[HRDPS]]
        RDPS: ClassVar[type[RDPS]]
        GDPS: ClassVar[type[GDPS]]

    @classmethod
    def available_models(cls) -> list[str]:
        """Return a sorted list of all registered model names."""
        from herbie.v2._base import HerbieModel

        return sorted(
            name
            for name, obj in vars(cls).items()
            if isinstance(obj, type) and issubclass(obj, HerbieModel)
        )

    def __class_getitem__(cls, item):
        """Allow ``Herbie["HRRR"]`` as an alias for ``Herbie.HRRR``."""
        return getattr(cls, item)

"""
Herbie namespace class.

``herbie.v2.__init__`` discovers all ``HerbieModel`` subclasses in the
``models/`` package and attaches them as class attributes of ``Herbie``.

This gives users three equivalent calling styles::

    from herbie.v2 import Herbie
    H = Herbie.HRRR("2025-01-01", fxx=6)   # namespace style

    from herbie.v2 import HRRR
    H = HRRR("2025-01-01", fxx=6)           # direct style

    import herbie.v2 as herbie
    H = herbie.HRRR("2025-01-01", fxx=6)   # module attribute style
"""

from __future__ import annotations


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
        H = HRRR("2025-01-01", fxx=6)
    """

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

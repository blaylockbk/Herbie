"""
Import all the model template classes.

A Herbie object specifies the
template by setting ``model='template_class_name'``. For example:

    Herbie('2022-01-01', model='hrrr')

Where "hrrr" is the name of the template class located in models/hrrr.py.
"""

import sys
from importlib.metadata import entry_points

from herbie import _config_path
from herbie.misc import ANSI

# ======================================================================
#                     Import Herbie Model Templates
# ======================================================================
from .cfs import *
from .ecmwf import *
from .gdps import *
from .gefs import *
from .gfs import *
from .hafs import *
from .hiresw import *
from .hrdps import *
from .href import *
from .hrrr import *
from .nam import *
from .nbm import *
from .nexrad import *
from .rap import *
from .rdps import *
from .rrfs import *
from .rtma import *
from .urma import *
from .usnavy import *


# ======================================================================
#                   Import Custom Templates from Plugins
# ======================================================================

for ep in entry_points(group="herbie.plugins"):
    cls = ep.load()
    globals()[cls.__name__] = cls
    print(
        f"""Herbie: Added model {ANSI.green}"{cls.__name__}"{ANSI.reset} """
        f"from {ANSI.blue}{ep.dist.name}{ANSI.reset}."
    )


# ======================================================================
#                     Import Private Model Templates
# ======================================================================

# TODO: Remove this in future release in favor of Herbie plugins.

_custom_template_file = _config_path / "custom_template.py"

try:
    if _custom_template_file.exists():
        warnings.warn(
            "Herbie: Custom model templates in the config path is deprecated. Please use a Herbie plugin: "
            "https://github.com/blaylockbk/herbie-plugin-tutorial",
            DeprecationWarning,
            stacklevel=2,
        )
        sys.path.insert(1, str(_custom_template_file.parent))
        from custom_template import *
except Exception:
    print(
        f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
        f" │ WARNING: Could not load custom template from         │\n"
        f" │ {ANSI.orange}{str(_custom_template_file):^50s}{ANSI.reset}   │\n"
        f" ╰──────────────────────────────────────────────────────╯\n"
    )

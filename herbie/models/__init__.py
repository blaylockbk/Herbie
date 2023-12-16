"""
Import all the model template classes. A Herbie object specifies the
template by setting ``model='template_class_name'``. For example:

    Herbie('2022-01-01', model='hrrr')

Where "hrrr" is the name of the template class located in models/hrrr.py.
"""

import sys
from pathlib import Path

from herbie import _config_path
from herbie.misc import ANSI

# ======================================================================
#                     Import Public Model Templates
# ======================================================================
from .ecmwf import *
from .gefs import *
from .gfs import *
from .hafs import *
from .hrdps import *
from .hrrr import *
from .nam import *
from .navgem import *
from .nbm import *
from .nexrad import *
from .nogaps import *
from .rap import *
from .rrfs import *
from .rtma import *
from .urma import *

# ======================================================================
#                     Import Private Model Templates
# ======================================================================
_custom_template_file = _config_path / "custom_template.py"

try:
    if _custom_template_file.exists():
        sys.path.insert(1, str(_custom_template_file.parent))
        from custom_template import *
except:
    print(
        f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
        f" │ WARNING: Could not load custom template from         │\n"
        f" │ {ANSI.orange}{str(_custom_template_file):^50s}{ANSI.reset}   │\n"
        f" ╰──────────────────────────────────────────────────────╯\n"
    )

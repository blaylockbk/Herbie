"""
Import all the model template classes. A Herbie object specifies the
template by setting ``model='template_class_name'``. For example:

    Herbie('2022-01-01', model='hrrr')

Where "hrrr" is the name of the template class located in models/hrrr.py.
"""

from pathlib import Path
import sys

# ======================================================================
#                     Import Public Model Templates
# ======================================================================
from .hrrr import *
from .gfs import *
from .nam import *
from .navgem import *
from .nogaps import *
from .nbm import *
from .nexrad import *
from .rap import *
from .rrfs import *
from .ecmwf import *
from .gefs import *
from .rtma import *
from .urma import *
from .hrdps import *
from .hafs import *

# ======================================================================
#                     Import Private Model Templates
# ======================================================================
_custom_template_file = Path("~/.config/herbie/custom_template.py").expand()

if _custom_template_file.exists():
    try:
        sys.path.insert(1, str(_custom_template_file.parent))
        from custom_template import *
    except:
        print(f"🤕 Herbie could not load custom template from {_custom_template_file}.")

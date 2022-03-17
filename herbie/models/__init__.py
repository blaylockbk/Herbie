"""
Import all the model template classes. A Herbie object specifies the
template by setting ``model='template_class_name'``. For example:

    Herbie('2022-01-01', model='hrrr')

Where `hrrr` is the name of the template class.
"""

from pathlib import Path

# ======================================================================
# Import Public Model Templates
# ======================================================================
from .gfs import *
from .hrrr import *
from .navgem import *
from .nbm import *
from .nexrad import *
from .rap import *
from .rrfs import *
from .ecmwf import *

# ! Th local.py file is only left for demonstration.
# ! You should copy the local template to a private template.
# from .local import *


# ======================================================================
# Import Private Model Templates
# ======================================================================
# To use custom templates, the following two files must exist
#
#     ~/.config/herbie/custom_template.py  ::  contianing a model template class
#     ~/.config/herbie/__init__.py         ::  empty file

_custom_template_file = Path("~/.config/herbie/custom_template.py").expand()

if _custom_template_file.exists():
    try:
        import sys

        sys.path.insert(1, str(_custom_template_file.parent))
        from custom_template import *

        print("🥳 Herbie loaded your custom templates.")
    except:
        print("🤕 Herbie could not load Custom templates.")

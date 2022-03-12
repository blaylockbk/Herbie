from pathlib import Path
import sys

# Import all model template files
from .gfs import *
from .hrrr import *
from .navgem import *
from .nbm import *
from .nexrad import *
from .rap import *
from .rrfs import *
from .ecmwf import *

try:
    # An experimental special case for locally stored files.
    from .local import *
except:
    pass

try:
    # Brian's personal local special case (hidden).
    from .local_B import *
except:
    pass

#==============================================================================
# Load Custom Template
#==============================================================================
# To use custom templates, the following files must exist
# - ~/.config/herbie/HerbieCustom.py
# - ~/.config/herbie/__init__.py

_custom_template_file = Path("~/.config/herbie/HerbieCustom.py").expand()

if _custom_template_file.exists():
    try:
        sys.path.insert(1, str(_custom_template_file.parent))
        from HerbieCustom import *
        print("🥳 Herbie loaded your custom templates.")
    except:
        print("🤕 Herbie could not load Custom templates.")

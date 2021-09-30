# Import all model template files
from .gfs import *
from .hrrr import *
from .rap import *
from .rrfs import *
from .nbm import *
from .navgem import *
try:
    # An experimental special case.
    from .local import *
except:
    pass

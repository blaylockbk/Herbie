# Import all model template files
from .gfs import *
from .gfs_wave import *
from .hrrr import *
from .hrrrak import *
from .rap import *
from .rrfs import *
from .nbm import *
from .navgem import *
try:
    # An experimental special case.
    from .local import *
except:
    pass

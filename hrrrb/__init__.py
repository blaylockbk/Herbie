## Brian Blaylock
## April 28, 2021

import warnings

# Try to import the hrrrb custom xarray accessors when any hrrrb module is loaded.
try:
    import hrrrb.accessors
except:
    warnings.warn('hrrrb custom accessors not imported')
    pass
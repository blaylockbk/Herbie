## Brian Blaylock
## April 28, 2021

import warnings
import configparser
import os
from pathlib import Path


########################################################################
# Load custom xarray accessors
try:
    import herbie.accessors
except:
    warnings.warn(
        "herbie xarray accessors could not be imported."
        "You are probably missing the Carpenter_Workshop."
        "If you want to use these functions, try"
        "`pip install git+https://github.com/blaylockbk/Carpenter_Workshop.git`"
        )
    pass

########################################################################
# Append Path object with my custom expand method so user can use
# environment variables in the config file (e.g., ${HOME}).
def _expand(self):
    """
    Fully expand and resolve the Path with the given environment variables.
    
    Example
    -------
    >>> Path('$HOME').expand()
    >>> PosixPath('/p/home/blaylock')
    """
    return Path(os.path.expandvars(self)).expanduser().resolve()

Path.expand = _expand

########################################################################
# Configure Herbie
# Configuration file is save in `~/config/herbie/config.cfg`
# `_default_save_dir` is the default path to save GRIB2 files.
config = configparser.ConfigParser()
_config_path = Path('~/.config/herbie/config.cfg').expand()

########################################################################
# Default Configuration Values
defaults = dict(
    data_dir = str(Path('~/data').expand()),
    priority = ','.join(['aws', 'nomads', 'google', 'azure', 'pando', 'pando2'])
)

########################################################################
# If a config file isn't found, make one
if not _config_path.exists():
    _config_path.parent.mkdir(parents=True, exist_ok=True)
    _config_path.touch()
    config.read(_config_path)
    config.add_section('download')
    config.set('download', 'default_save_dir', defaults['data_dir'])
    config.set('download', 'default_priority', defaults['priority'])
    with open(_config_path, 'w') as configfile:
        config.write(configfile)
    print(f'⚙ Created config file [{_config_path}]',
          f'with default download directory set as [{defaults["data_dir"]}]', 
          f'and default source priority as [{defaults["priority"]}]')


########################################################################
# Read the config file
config.read(_config_path)

try:
    _default_save_dir = Path(config.get('download', 'default_save_dir')).expand()
    _default_priority = config.get('download', 'default_priority').split(',')
except:
    print(f'🦁🐯🐻 oh my! {_config_path} looks weird,',
          f'but I will add new settings')
    try:
        config.add_section('download')
    except:
        pass  # section already exists
    config.set('download', 'default_save_dir', defaults['data_dir'])
    config.set('download', 'default_priority', defaults['priority'])
    with open(_config_path, 'w') as configfile:
        config.write(configfile)
    _default_save_dir = Path(config.get('download', 'default_save_dir'))
    _default_priority = config.get('download', 'default_priority').split(',')
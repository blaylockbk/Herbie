"""
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██

                █ ██
                █ ██ ┏━┓ ┏━┓            ┏━┓   ┏━┓
                █ ██ ┃ ┃ ┃ ┃┏━━━━┓┏━┓┏━┓┃ ┃   ┏━┓┏━━━━┓
                █ ██ ┃ ┗━┛ ┃┃ ━━ ┃┃ ┏━━┛┃ ┗━━┓┃ ┃┃ ━━ ┃
                █ ██ ┃ ┏━┓ ┃┃ ━━━┓┃ ┃   ┃ ━━ ┃┃ ┃┃ ━━━┓
                █ ██ ┗━┛ ┗━┛┗━━━━┛┗━┛   ┗━━━━┛┗━┛┗━━━━┛
                █ ██
                       🏁 Retrieve NWP Model Data 🏁

██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██  ██
"""

import os
from pathlib import Path

import toml

from herbie.misc import ANSI

__author__ = "Brian K. Blaylock"
__meet_Herbie__ = "https://en.wikipedia.org/wiki/Herbie"
__movie_clips__ = "https://youtube.com/playlist?list=PLrSOkJxBTv53gvwbw9pVlMm-1C2PUHJx7"

try:
    ## TODO: Will the `_version.py` file *always* be present?
    ## TODO: What if the person doesn't do "pip install"
    from ._version import __version__, __version_tuple__
except:
    __version__ = "unknown"
    __version_tuple__ = (999, 999, 999)


########################################################################
# Overload Path object with my custom `expand` method so the user can
# set environment variables in the config file (e.g., ${HOME}).
def _expand(self, resolve=False, absolute=False):
    """
    Fully expand the Path with the given environment variables.

    Optionally, resolve the path.

    Example
    -------
    >>> Path('$HOME').expand()
    Results in PosixPath('/p/home/blaylock')
    """
    p = Path(os.path.expandvars(self)).expanduser()

    if resolve:
        # TODO Why does this get stuck sometimes??
        p = p.resolve()

    if absolute:
        p = p.absolute()

    return p


Path.expand = _expand

########################################################################
# Location of Herbie's configuration file
_config_path = os.getenv("HERBIE_CONFIG_PATH", "~/.config/herbie")
_config_path = Path(_config_path).expand()
_config_file = _config_path / "config.toml"

# Default directory Herbie saves model output
# NOTE: The `\\` is an escape character in TOML.
#       For Windows paths, "C:\\user\\"" needs to be "C:\\\\user\\\\""
_save_dir = os.getenv("HERBIE_SAVE_DIR", "~/data")
_save_dir = Path(_save_dir).expand()
_save_dir = str(_save_dir).replace("\\", "\\\\")

# Default TOML Configuration Values
default_toml = f"""# Herbie defaults

[default]
model = "hrrr"
fxx = 0
save_dir = "{_save_dir}"
overwrite = false
verbose = true

# =============================================================================
# You can set the priority order for checking data sources.
# If you don't specify a default priority, Herbie will check each source in the
# order listed in the model template file. Beware: setting a default priority
# might prevent you from checking all available sources.
#
#priority = ['aws', 'nomads', 'google', 'etc.']

"""

# Default `custom_template.py` placeholder
default_custom_template = """
# ======================
# Private Model Template
# ======================
# Read more details at
# https://herbie.readthedocs.io/en/stable/user_guide/extend.html

# Uncomment and edit the class below, add additional classes, and edit
# the SOURCES dictionary to help Herbie locate your locally stored GRIB2
# files.

'''
class model1_name:
    def template(self):
        self.DESCRIPTION = "Local GRIB Files for model1"
        self.DETAILS = {
            "local_main": "These GRIB2 files are from a locally-stored modeling experiments."
            "local_alt": "These GRIB2 files are an alternative location for these model files."
        }

        # These PRODUCTS are optional but can provide an additional parameter to search for files.
        self.PRODUCTS = {
            "prs": "3D pressure level fields",
            "sfc": "Surface level fields",
        }

        # These are the paths to your local GRIB2 files.
        self.SOURCES = {
            "local_main": f"/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
'''
"""

########################################################################
# Load config file (create one if needed)
try:
    # Load the Herbie config file
    config = toml.load(_config_file)
except:
    try:
        # Create the Herbie config file
        _config_path.mkdir(parents=True, exist_ok=True)
        with open(_config_file, "w", encoding="utf-8") as f:
            f.write(default_toml)

        # Create `custom_template.py` placeholder
        _init_path = _config_path / "__init__.py"
        _custom_path = _config_path / "custom_template.py"
        if not _init_path.exists():
            with open(_init_path, "w") as f:
                pass
        if not _custom_path.exists():
            with open(_custom_path, "w") as f:
                f.write(default_custom_template)

        print(
            f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
            f" │ INFO: Created a default config file.                 │\n"
            f" │ You may view/edit Herbie's configuration here:       │\n"
            f" │ {ANSI.orange}{str(_config_file):^50s}{ANSI.reset}   │\n"
            f" ╰──────────────────────────────────────────────────────╯\n"
        )

        # Load the new Herbie config file
        config = toml.load(_config_file)
    except (FileNotFoundError, PermissionError, IOError):
        print(
            f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
            f" │ WARNING: Unable to create config file               │\n"
            f" │ {ANSI.orange}{str(_config_file):^50s}{ANSI.reset}   │\n"
            f" │ Herbie will use standard default settings.           │\n"
            f" │ Consider setting env variable HERBIE_CONFIG_PATH.    │\n"
            f" ╰──────────────────────────────────────────────────────╯\n"
        )
        config = toml.loads(default_toml)


# Expand the full path for `save_dir`
config["default"]["save_dir"] = Path(config["default"]["save_dir"]).expand()

if os.getenv("HERBIE_SAVE_DIR"):
    config["default"]["save_dir"] = Path(os.getenv("HERBIE_SAVE_DIR")).expand()
    print(
        f" ╭─{ANSI.herbie}─────────────────────────────────────────────╮\n"
        f" │ INFO: Overriding the configured save_dir because the │\n"
        f" │ environment variable HERBIE_SAVE_DIR is set to       │\n"
        f" │ {ANSI.orange}{os.getenv('HERBIE_SAVE_DIR'):^50s}{ANSI.reset}   │\n"
        f" ╰──────────────────────────────────────────────────────╯\n"
    )

from herbie.core import Herbie
from herbie.fast import FastHerbie, Herbie_latest
from herbie.wgrib2 import wgrib2

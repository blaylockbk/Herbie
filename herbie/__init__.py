## Brian Blaylock
## April 28, 2021

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

__author__ = "Brian K. Blaylock"
__meet_Herbie__ = "https://en.wikipedia.org/wiki/Herbie"
__movie_clips__ = "https://youtube.com/playlist?list=PLrSOkJxBTv53gvwbw9pVlMm-1C2PUHJx7"

try:
    ## TODO: Will the `_version.py` file *always* be present? What if the
    ## TODO:   person doesn't do "install"
    from ._version import __version__, __version_tuple__
except:
    __version__ = "unknown"
    __version_tuple__ = (999, 999, 999)


########################################################################
# Append Path object with my custom expand method so user can use
# environment variables in the config file (e.g., ${HOME}).
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
# Herbie configuration file
# Configuration file is save in `~/config/herbie/config.toml`
_config_path = Path("~/.config/herbie/config.toml").expand()

# NOTE: The `\\` is an escape character in TOML.
# For Windows paths "C:\\user\\"" needs to be "C:\\\\user\\\\""
_save_dir = str(Path("~/data").expand())
_save_dir = _save_dir.replace("\\", "\\\\")


########################################################################
# Default TOML Configuration Values
default_toml = f"""
[default]
model = "hrrr"
fxx = 0
save_dir = "{_save_dir}"
overwrite = false
verbose = true
"""

########################################################################
# Default custom_template.py placeholder
default_custom_template = """
# ======================
# Private Model Template
# ======================
# Find more details at
# https://herbie.readthedocs.io/user_guide/extend.html

# Uncomment class, add additional classes, and edit SOURCES dictionary
# to help Herbie locate your locally stored GRIB2 files.

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
        self.SOURCES = {
            "local_main": f"/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
            "local_alt": f"/alternative/path/to/your/model1/templated/with/{self.model}/gribfiles/{self.date:%Y%m%d%H}/nest{self.nest}/the_file.t{self.date:%H}z.{self.product}.f{self.fxx:02d}.grib2",
        }
        self.LOCALFILE = f"{self.get_remoteFileName}"
'''
"""

########################################################################
# If a config file isn't found, make one
if not _config_path.exists():
    print(
        f" ╭─────────────────────────────────────────────────╮\n"
        f" │ I'm building Herbie's default config file.      │\n"
        f" ╰╥────────────────────────────────────────────────╯\n"
        f" 👷🏻‍♂️"
    )

    # Create config.toml file
    _config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(_config_path, "w", encoding="utf-8") as f:
        toml_string = toml.dump(toml.loads(default_toml), f)

    # Create custom_template.py placeholder
    _init_path = _config_path.parent / "__init__.py"
    _custom_path = _config_path.parent / "custom_template.py"
    if not _init_path.exists():
        with open(_init_path, "w") as f:
            pass
    if not _custom_path.exists():
        with open(_custom_path, "w") as f:
            f.write(default_custom_template)

    print(
        f" ╭─────────────────────────────────────────────────╮\n"
        f" │ You're ready to go.                             │\n"
        f" │ You may edit the config file here:              │\n"
        f" │ {str(_config_path):<45s}   │\n"
        f" ╰╥────────────────────────────────────────────────╯\n"
        f" 👷🏻‍♂️"
    )


########################################################################
# Read the config file
config = toml.load(_config_path)

config["default"]["save_dir"] = Path(config["default"]["save_dir"]).expand()


from herbie.core import Herbie
from herbie.fast import FastHerbie, Herbie_latest
from herbie.wgrib2 import wgrib2

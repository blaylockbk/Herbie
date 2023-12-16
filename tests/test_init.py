import os

import toml

from herbie import Path, default_toml


def test_Path_expand():
    """Test custom Path().expand() method.

    Yes, it's probably not great practice to override a
    built-in module, but for me, this is an added level
    of convenience.
    """
    a = Path("~/test/dir").expand()
    b = Path("~/test/dir").expanduser()
    assert a == b

    a = Path("$HOME/test/dir").expand()
    b = Path(os.path.expandvars("$HOME/test/dir"))
    assert a == b


def test_default_toml():
    # Confirm that default_toml is valid
    a = toml.loads(default_toml)

    a["default"]["model"] == "hrrr"
    a["default"]["fxx"] == 0
    a["default"]["overwrite"] == False
    a["default"]["verbose"] == True

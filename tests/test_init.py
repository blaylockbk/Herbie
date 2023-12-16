import toml

from herbie import default_toml


def test_default_toml():
    # Confirm that default_toml is valid
    a = toml.loads(default_toml)

    a["default"]["model"] == "hrrr"
    a["default"]["fxx"] == 0
    a["default"]["overwrite"] == False
    a["default"]["verbose"] == True

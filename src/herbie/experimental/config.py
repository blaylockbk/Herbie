import os
import tomllib
from copy import deepcopy
from pathlib import Path

# Hardcoded reasonable defaults
DEFAULT_CONFIG = {
    "default": {
        "model": "hrrr",
        "product": "prs",
        "step": 0,
        "save_dir": "~/herbie-data",
    }
}

def deep_update(mapping, *updating_mappings):
    """
    Update a nested dictionary.
    """
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if k in updated_mapping and isinstance(updated_mapping[k], dict) and isinstance(v, dict):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping

def load_toml(path: Path) -> dict:
    """Load a TOML file if it exists, return empty dict if not."""
    if not path.is_file():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        # Ignore malformed files for now
        return {}

def get_config() -> dict:
    """
    Load Herbie configuration by cascading through:
    1. Hardcoded defaults
    2. ~/.config/herbie/herbie.toml (or HERBIE_CONFIG_PATH/herbie.toml)
    3. pyproject.toml ([tool.herbie])
    4. ./herbie.toml
    5. Environment variable overrides (HERBIE_SAVE_DIR)
    """
    config = deepcopy(DEFAULT_CONFIG)

    # 2. Global config file
    config_dir_env = os.getenv("HERBIE_CONFIG_PATH")
    if config_dir_env:
        global_config_path = Path(config_dir_env).expanduser() / "herbie.toml"
    else:
        global_config_path = Path("~/.config/herbie/herbie.toml").expanduser()

    global_config = load_toml(global_config_path)
    if global_config:
        config = deep_update(config, global_config)

    # 3. pyproject.toml
    pyproject_path = Path("pyproject.toml")
    pyproject_data = load_toml(pyproject_path)
    if pyproject_data and "tool" in pyproject_data and "herbie" in pyproject_data["tool"]:
        config = deep_update(config, pyproject_data["tool"]["herbie"])

    # 4. Local herbie.toml
    local_config_path = Path("herbie.toml")
    local_config = load_toml(local_config_path)
    if local_config:
        config = deep_update(config, local_config)

    # 5. Environment overrides
    save_dir_env = os.getenv("HERBIE_SAVE_DIR")
    if save_dir_env:
        if "default" not in config:
            config["default"] = {}
        config["default"]["save_dir"] = save_dir_env

    # Expand save_dir user path (e.g. ~/dir -> /home/user/dir)
    if "save_dir" in config.get("default", {}):
        config["default"]["save_dir"] = str(Path(config["default"]["save_dir"]).expanduser())

    return config

# Load config once on module import
settings = get_config()

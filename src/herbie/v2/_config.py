"""
Configuration loading for Herbie v2.

Priority (lowest → highest):
  1. Hardcoded defaults
  2. ~/.config/herbie/herbie.toml
  3. pyproject.toml [tool.herbie]
  4. ./herbie.toml
  5. HERBIE_SAVE_DIR environment variable
"""

from __future__ import annotations

import os
import tomllib
from copy import deepcopy
from pathlib import Path

_DEFAULTS: dict = {
    "save_dir": "~/herbie-data",
    "overwrite": False,
    "priority": None,  # None means use each model's source dict order
    "index_fallback_method": "auto",
}


def _load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _deep_update(base: dict, update: dict) -> dict:
    result = base.copy()
    for k, v in update.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_update(result[k], v)
        else:
            result[k] = v
    return result


def load_config() -> dict:
    cfg = deepcopy(_DEFAULTS)

    # Global config file
    config_dir = os.getenv("HERBIE_CONFIG_PATH")
    global_path = (
        Path(config_dir).expanduser() / "herbie.toml"
        if config_dir
        else Path("~/.config/herbie/herbie.toml").expanduser()
    )
    cfg = _deep_update(cfg, _load_toml(global_path))

    # pyproject.toml [tool.herbie]
    pp = _load_toml(Path("pyproject.toml"))
    if herbie_cfg := pp.get("tool", {}).get("herbie"):
        cfg = _deep_update(cfg, herbie_cfg)

    # Local herbie.toml
    cfg = _deep_update(cfg, _load_toml(Path("herbie.toml")))

    # Environment overrides
    if save_dir_env := os.getenv("HERBIE_SAVE_DIR"):
        cfg["save_dir"] = save_dir_env

    cfg["save_dir"] = str(Path(cfg["save_dir"]).expanduser())
    return cfg


# Loaded once at import time
CONFIG = load_config()

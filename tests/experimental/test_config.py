import os
from pathlib import Path

import pytest
import tomllib

from herbie.experimental import config
from herbie.experimental import Herbie


def test_default_config_loading():
    """Verify hardcoded defaults are loaded when no files exist."""
    # Force a fresh load without environment variables
    # We do a mock here just to see what the config returns natively
    os.environ.pop("HERBIE_SAVE_DIR", None)
    os.environ.pop("HERBIE_CONFIG_PATH", None)

    settings = config.get_config()

    assert "default" in settings
    assert settings["default"]["model"] == "hrrr"
    assert settings["default"]["product"] == "prs"
    assert settings["default"]["step"] == 0
    assert "herbie-data" in settings["default"]["save_dir"]


def test_env_save_dir_override():
    """Verify HERBIE_SAVE_DIR environment variable overrides all other defaults."""
    os.environ["HERBIE_SAVE_DIR"] = "/tmp/env_test_dir"

    settings = config.get_config()
    os.environ.pop("HERBIE_SAVE_DIR", None)  # Clean up

    assert settings["default"]["save_dir"] == "/tmp/env_test_dir"


@pytest.fixture
def mock_toml_files(monkeypatch, tmp_path):
    """
    Mock the pathlib glob/existence to point to our temp dir.
    We just mock `config.load_toml` to read from our test fixtures.
    """
    original_load = config.load_toml

    # Store config mock data
    mock_data = {
        "global": None,
        "pyproject": None,
        "local": None
    }

    def mock_load_toml(path: Path):
        path_str = str(path)
        if "herbie.toml" in path_str and "config" in path_str:
            return mock_data["global"] or {}
        elif "pyproject.toml" in path_str:
            return mock_data["pyproject"] or {}
        elif "herbie.toml" in path_str and "config" not in path_str:
            return mock_data["local"] or {}
        return {}

    monkeypatch.setattr(config, "load_toml", mock_load_toml)
    return mock_data


def test_config_precedence(mock_toml_files):
    """Verify config dictionaries override each other in the correct order."""

    # 1. Base default is model="hrrr", product="prs"

    # 2. Global file overrides product
    mock_toml_files["global"] = {"default": {"product": "sfc"}}
    settings = config.get_config()
    assert settings["default"]["product"] == "sfc"
    assert settings["default"]["model"] == "hrrr" # Still default

    # 3. Pyproject overrides global
    mock_toml_files["pyproject"] = {"tool": {"herbie": {"default": {"product": "nat", "model": "gfs"}}}}
    settings = config.get_config()
    assert settings["default"]["product"] == "nat"
    assert settings["default"]["model"] == "gfs"

    # 4. Local overrides pyproject
    mock_toml_files["local"] = {"default": {"model": "ecmwf", "step": 12}}
    settings = config.get_config()
    assert settings["default"]["model"] == "ecmwf"  # From local
    assert settings["default"]["product"] == "nat"  # From pyproject
    assert settings["default"]["step"] == 12        # From local


def test_herbie_init_kwargs_filtering():
    """
    Verify that global config defaults (like product='prs') do not
    break models that configure entirely different valid options.
    """
    # GFS doesn't have "prs" as a valid product, it uses "pgrb2"

    # If filtering works, Herbie initialization won't throw a ValueError
    H = Herbie("2024-01-01", model="gfs")
    assert H.model_name == "GFS"

    # If the user explicitly passes something invalid, it SHOULD raise
    with pytest.raises(ValueError, match="Invalid product 'invalid_product'"):
        Herbie("2024-01-01", model="gfs", product="invalid_product")

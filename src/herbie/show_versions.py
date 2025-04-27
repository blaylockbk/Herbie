import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys

import herbie


def show_versions():
    """
    Print version info for Herbie and all known dependencies.

    There are a few ways to use this.

    ```python
    # In a Python script
    from herbie
    herbie.show_versions()
    ```

    ```bash
    # in the terminal
    herbie --show-versions

    # using uv
    uv run herbie --show-versions
    ```
    """
    core_packages = [
        "cfgrib",
        "eccodes",
        "numpy",
        "pandas",
        "requests",
        "toml",
        "xarray",
    ]
    optional_packages = [
        "cartopy",
        "ipykernel",
        "matplotlib",
        "metpy",
        "pygrib",
        "pyproj",
        "scikit-learn",
    ]

    def print_package_versions(packages, title):
        print(f"\n{title}:")
        for pkg in packages:
            try:
                version = importlib.metadata.version(pkg)
                print(f"{pkg:20} {version}")
            except importlib.metadata.PackageNotFoundError:
                print(f"{pkg:20} Not installed")

    print("\nOPERATING SYSTEM:")
    print(platform.platform())

    print("\nPYTHON VERSION:")
    print(sys.version)

    print("\nHERBIE VERSION:")
    print(herbie.__version__)

    print_package_versions(core_packages, "CORE DEPENDENCIES")
    print_package_versions(optional_packages, "OPTIONAL DEPENDENCIES")

    print("\nOTHER SOFTWARE:")
    try:
        result = subprocess.run(["curl", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0]
            path = shutil.which("curl")
            print(f"{'curl':20} {first_line.strip().split()[1]} [{path}]")
        else:
            print(f"{'curl':20} Found but failed to get version")
    except FileNotFoundError:
        print(f"{'curl':20} Not found")

    try:
        result = subprocess.run(["wgrib2", "--version"], capture_output=True, text=True)
        if result.returncode == 8:
            first_line = result.stdout.splitlines()[0]
            path = shutil.which("wgrib2")
            print(f"{'wgrib2':20} {first_line.strip().split()[0]} [{path}]")
        else:
            print(f"{'wgrib2':20} Found but failed to get version")
    except FileNotFoundError:
        print(f"{'wgrib2':20} Not found")

    print()


if __name__ == "__main__":
    show_versions()

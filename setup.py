from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf8")

setup(
    name="herbie-data",  # Unfortunately, "herbie" is already used.
    version="0.0.10",
    author="Brian K. Blaylock",
    author_email="blaylockbk@gmail.com",
    description="Download model data (HRRR, RAP, GFS, NBM, etc.) from NOMADS, NOAA's Big Data Program partners (Amazon, Google, Microsoft), and the University of Utah Pando Archive System.",
    long_description=README,
    long_description_content_type="text/markdown",
    project_urls={
        "Source Code": "https://github.com/blaylockbk/Herbie",
        "Documentation": "https://blaylockbk.github.io/Herbie/_build/html/",
    },
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "numpy",
        "pandas",
        "xarray",
        "cfgrib",
        "metpy",
        "cartopy",
        "toml",
        "pygrib",
    ],
    keywords=[
        "xarray",
        "meteorology",
        "weather",
        "HRRR",
        "GRIB2",
        "numerical weather prediction",
        "forecast",
        "atmosphere",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering :: Atmospheric Science",
    ],
    zip_safe=False,
)

###############################################################################
## Brian's Note: How to upload a new version to PyPI
## -------------------------------------------------
# Created a new conda environment with twine
# conda create -n pypi python=3 twine pip -c conda-forge
"""
conda env update -f Carpenter_Workshop/environments/pypi.yml

conda activate pypi
cd Herbie
python setup.py sdist bdist_wheel
twine check dist/*

# PyPI
twine upload --skip-existing dist/*

# Test PyPI
twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*
"""

# See download statistics at: https://pepy.tech/project/herbie-data

# Check import time with python -X importtime herbie/archive.py > importtime.txt 2>&1


#######################################################
## On May 12, 2022 I changed the default branch to main
## You can change your local clone default name with
## The following
"""
git branch -m master main
git fetch origin
git branch -u origin/main main
git remote set-head origin -a
"""

from setuptools import setup

if __name__ == "__main__":
    setup()

###############################################################################
## Brian's Note: How to upload a new version to PyPI
## -------------------------------------------------
# Update version in
#  - setup.py
#  - CITATION.cff
#  - Create a tag and release in GitHub
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
## the following
"""
git branch -m master main
git fetch origin
git branch -u origin/main main
git remote set-head origin -a
"""

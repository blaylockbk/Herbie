_Notes for when Brian needs to publish a new release_.

# How to publish the `herbie-data` package

## Pre-step 
Update Herbie version number in
- ~~setup.py~~
- CITATION.cff
- Create a tag and release in GitHub

## 📦 Publish to PyPI

Created a new conda environment with twine

```bash
# To create an environment for publishing to PyPI
conda create -n pypi python=3 twine pip -c conda-forge

# To update that conda environment
conda update -n pypi --all
```


```bash
# Build the package for PyPI
conda activate pypi
cd Herbie
python setup.py sdist bdist_wheel
twine check dist/*
```

> Or, should I be using this https://github.com/pypa/build


### Upload Package to PyPI
```bash
twine upload --skip-existing dist/*

# followed by username/password
```

### Upload Package to Test PyPI
```bash
twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

# followed by username and password
```

## 🐍 Publish to Conda
Go to herbie-data feedstock, update the version.

(More details coming soon)

-----------

# Miscellaneous

See PyPI download statistics at: https://pepy.tech/project/herbie-data



Check import time with 

```bash
python -X importtime herbie/archive.py > importtime.txt 2>&1
```



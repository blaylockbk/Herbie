_Notes for when Brian needs to publish a new release_.

# How to publish a new release of the `herbie-data` package

## Pre-step

Update Herbie version number in

- ~~setup.py~~
- ./CITATION.cff
- ./docs/conf.py
- Build the docs (one last time before release)
- **Create a tag and release in GitHub**

## 📦 Publish to PyPI

Created a new conda environment with twine, pip, and build

```bash
# To create an environment for publishing to PyPI
conda create -n pypi python=3 twine pip build -c conda-forge

# To update that conda environment
conda update -n pypi --all
```

```bash
## THIS IS OLD; DO NOT USE
# Build the package for PyPI
conda activate pypi
cd Herbie
python setup.py sdist bdist_wheel
twine check dist/*
```

**NEW** - Using the [build](https://github.com/pypa/build) tool to build my package following the steps from [here](https://towardsdatascience.com/how-to-package-your-python-code-df5a7739ab2e)

```bash
conda activate pypi
cd Herbie
python -m build
twine check dist/*
```

### Upload Package PyPI

```bash
# Upload to TEST PyPI site
twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

# followed by username and password
```

```bash
# Upload to REAL PyPI site
twine upload --skip-existing dist/*

# followed by username/password
```


## 🐍 Publish to Conda

Go to herbie-data feedstock, update the version.

(More details coming soon)

---

# Miscellaneous

See PyPI download statistics at: https://pepy.tech/project/herbie-data

Check import time with

```bash
python -X importtime herbie/archive.py > importtime.txt 2>&1
```

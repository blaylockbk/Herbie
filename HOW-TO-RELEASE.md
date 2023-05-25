# _Note to self_
# How to publish a new release of the `herbie-data` package on PyPI and conda-forge

## Pre-step

Update Herbie version number in

- Update `./CITATION.cff` citation document
- Update `./docs/_static/switcher.json` with a new item for the version you will soon create
- Make sure all leftover changes on main are committed that you want. 
- **Create a tag and release in GitHub**. 

> Note: The tag name should follow the pattern `YYYY.MM.0`
> `YYYY` - Four-digit year the tag is created
> `MM` - Month number the tag is created with _no leading zeros_ (PyPI doesn't care about leading zeros).
> `0` - The micro update, used if there is more than one release in the same month (most likely due to a bug fix). 


## 📦 Publish to PyPI

On my local copy, do a `git fetch` and then checkout the tag. DO NOT EDIT ANY FILES (else you will get a `_post#` in the version name.)

Created a new conda environment with twine, pip, and build

```bash
# To create an environment for publishing to PyPI
conda create -n pypi python=3 twine pip build -c conda-forge

# To update that conda environment
conda update -n pypi -c conda-forge --all
python3 -m pip install --upgrade build  # Needed to get the latest version of build (0.10+)
python3 -m pip install --upgrade twine
```

Use the [build](https://github.com/pypa/build) tool to build my package following the steps from [here](https://towardsdatascience.com/how-to-package-your-python-code-df5a7739ab2e)

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

```
Enter username and password. _Note to self: I get a warning because I'm not using keyring_

Now confirm the file was uploaded to PyPI at <https://pypi.org/project/herbie-data/>

## 🐍 Publish to Conda

Go to herbie-data feedstock, update the version in the `meta.yml` file.

- Fork the [herbie-data Conda feedstock](https://github.com/conda-forge/herbie-data-feedstock/pull/1/checks?check_run_id=11936300099)
- Follow the instructions in the README to update the build
    - Update version
    - Update sha256 has for the `herbie-data-{version}.tar.gz` file (found on PyPI) in the "Download files" tab.
    - Set build to 0 for releasing a new version.
- Create pull request.
- Follow instructions in the pull request template.

---

# Miscellaneous

See PyPI download statistics at: https://pepy.tech/project/herbie-data

Check import time with

```bash
python -X importtime herbie/archive.py > importtime.txt 2>&1
```

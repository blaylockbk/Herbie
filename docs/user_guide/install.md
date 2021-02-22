# 🐍 Installation and Conda Environment

This package requires **Python 3.7+** (doesn't work in 3.6 and earlier because I use relative imports)

### Option 1: pip
Install the last published version from PyPI.

```bash
pip install hrrrb
```

But the version on PyPI has diverged a lot from the code on GitHub, so I would recommend not getting from PyPI. To get the most recent hrrrb code, you may install the package directly from GitHub

```bash
pip install git+https://github.com/blaylockbk/HRRR_archive_download.git
```

> Requires: xarray, cfgrib, pandas, cartopy, requests, curl  
> Optional: matplotlib, cartopy

### Option 2: conda
If conda environments are new to you, I suggest you become familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

I have provided a sample Anaconda [environment.yml](https://github.com/blaylockbk/HRRR_archive_download/blob/master/environment.yml) file that lists the minimum packages required plus some extras that might be useful when working with other types of weather data. Look at the bottom lines of that yaml file...there are two ways to install `hrrrb` with pip. Comment out the lines you don't want.

For the latest development code:
```yaml
- pip:
    - git+https://github.com/blaylockbk/HRRR_archive_download.git
```
For the latest published version
```yaml
- pip:
    - hrrrb
```

First, create the virtual environment with 

```bash
conda env create -f environment.yml
```

Then, activate the `hrrrb` environment. Don't confuse this _environment_ name with the _package_ name.

```bash
conda activate hrrrb
```

Occasionally, you might want to update all the packages in the environment.

```bash
conda env update -f environment.yml
```

### Alternative "Install" Method
There are several other ways to "install" a python package so you can import them. One alternatively is you can `git clone https://github.com/blaylockbk/HRRR_archive_download.git` this repository to any directory. To import the package, you will need to update your PYTHONPATH environment variable to find the directory you put this package or add the line `sys.path.append("/path/to/hrrrb")` at the top of your python script.


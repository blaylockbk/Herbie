# 🐍 Installation and Conda Environment

Herbie requires `curl` and **Python 3.8+** with the following packages: `requests`, `pandas`, `xarray`, and `cfgrib`. Optional packages are `matplotlib`, `cartopy`, and[`Carpenter_Workshop`](https://github.com/blaylockbk/Carpenter_Workshop).

### Option 1: pip

> Note: "herbie" is already registered on PyPI, so I continue to use the "hrrrb" package to publish for now. This may change in version 0.1.0

Install the last published version from PyPI.

```bash
pip install herbie-data
```

The version on PyPI has likely diverged from the code on GitHub, so to get the most recent Herbie code, install the package directly from GitHub.

```bash
pip install git+https://github.com/blaylockbk/Herbie.git
```

### Option 2: conda
If conda environments are new to you, I suggest you become familiar with [managing conda environments](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html).

I have provided a sample Anaconda [environment.yml](https://github.com/blaylockbk/Herbie/blob/master/environment.yml) file that lists the minimum packages required plus some extras that I find useful. Look at the bottom lines of that yaml file...there are two ways to install `hrrrb` with pip within the environment file. Comment out the line you don't want.

For the latest development code:
```yaml
- pip:
    - git+https://github.com/blaylockbk/Herbie.git
```
For the latest published version
```yaml
- pip:
    - herbie-data
```

First, create the virtual environment with 

```bash
conda env create -f environment.yml
```

Then, activate the `herbie` environment. Don't confuse this conda _environment_ name with the _package_ name.

```bash
conda activate herbie
```

Occasionally, you might want to update all the packages in the environment.

```bash
conda env update -f environment.yml
```

### Alternative "Install" Method
There are several other ways to "install" a python package so you can import them. One alternatively is you can clone the repository and put it in your PATH or PYTHONPATH.

```bash
git clone https://github.com/blaylockbk/Herbie.git
```
To import the package, you will need to update your `PYTHONPATH` environment variable to find the directory you put this package or add the line `sys.path.append("/path/to/herbie")` at the top of your python script.


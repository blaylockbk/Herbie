# 🐍 Installation

## conda install

[![Conda](https://img.shields.io/conda/v/conda-forge/herbie-data)](https://anaconda.org/conda-forge/herbie-data)

The easiest way to install Herbie and its dependencies is with [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) from conda-forge.

```bash
conda install -c conda-forge herbie-data
```

## pip install

[![PyPI - Version](https://img.shields.io/pypi/v/herbie-data)](https://pypi.org/project/herbie-data/)

Herbie is published on PyPI and you can install it with pip, _but_ it requires some dependencies that you will have to install yourself:

- Python 3.9+
- [cURL](https://anaconda.org/conda-forge/curl)
- [eccodes](https://anaconda.org/conda-forge/eccodes), which is required by [cfgrib](https://anaconda.org/conda-forge/cfgrib).
- _Optional:_ [wgrib2](https://anaconda.org/conda-forge/wgrib2)

When those are installed within your environment, _then_ you can install Herbie with pip.

```bash
# Install last published version
pip install herbie-data
```

To install the full functionality in the library which includes
[xarray accessors](https://github.com/blaylockbk/Herbie/blob/main/herbie/accessors.py) for plotting and data manipulation, please install the "extras" dependencies:

```bash
# Install last published version
pip install 'herbie-data[extras]'
```

The code can also be installed directly from github.

```bash
# Install current main branch
pip install git+https://github.com/blaylockbk/Herbie.git
```

or

```bash
# Clone and install editable source code
git clone https://github.com/blaylockbk/Herbie.git
cd Herbie
pip install -e .
```

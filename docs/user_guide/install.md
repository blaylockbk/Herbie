# 🐍 Installation

## conda install

[![Conda](https://img.shields.io/conda/v/conda-forge/herbie-data)](https://anaconda.org/conda-forge/herbie-data)

The easiest way to install Herbie and its dependencies is with [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) from conda-forge.

```bash
mamba install -c conda-forge herbie-data
```

```bash
conda install -c conda-forge herbie-data
```

## pip install

[![PyPI - Version](https://img.shields.io/pypi/v/herbie-data)](https://pypi.org/project/herbie-data/)

Herbie is published on PyPI and you can install it with pip, _but_ it requires some dependencies that you will have to install yourself:

- Python 3.10+
- _Optional:_ [wgrib2](https://anaconda.org/conda-forge/wgrib2)

When those are installed within your environment, _then_ you can install Herbie with pip.

```bash
# Install last published version
pip install herbie-data
```

To install the full functionality in the library which includes
[xarray accessors](https://github.com/blaylockbk/Herbie/blob/main/src/herbie/accessors.py) for plotting and data manipulation, please install the "extras" dependencies:

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

## uv install

You can add Herbie to your [uv](https://docs.astral.sh/uv/) project with:

```bash
uv add herbie-data
```

Herbie CLI tools can be installed with

```bash
uv tool install herbie-data
```

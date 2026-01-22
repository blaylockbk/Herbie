# 🐍 Installation

There are so many ways to install stuff. Pick the one that fits your workflow.

## Install with conda/mamba

[![Conda](https://img.shields.io/conda/v/conda-forge/herbie-data)](https://anaconda.org/conda-forge/herbie-data)

For conda/mamba users:

```bash
mamba install -c conda-forge herbie-data
```

```bash
conda install -c conda-forge herbie-data
```

## Install with uv

For [uv](https://docs.astral.sh/uv/) users, add herbie as a project dependency:

```bash
uv add herbie-data
```

The Herbie CLI may be installed as a tool:

```bash
uv tool install herbie-data
```

## Install with pip

[![PyPI - Version](https://img.shields.io/pypi/v/herbie-data)](https://pypi.org/project/herbie-data/)

For pip users:

```bash
# Install last release
pip install herbie-data
```

To install the full functionality which includes
[xarray accessors](https://github.com/blaylockbk/Herbie/blob/main/src/herbie/accessors.py) for plotting and data manipulation, please install the "extras" dependencies:

```bash
pip install 'herbie-data[extras]'
```

The latest updates can be installed directly from GitHub:

```bash
# Install current main branch
pip install git+https://github.com/blaylockbk/Herbie.git
```

---

## Optional Software: wgrib2

Herbie provides some very basic, limited wrappers for [wgrib2](https://wgrib2-docs.readthedocs.io/en/latest/). For Linux or Mac users, the easiest way to install wgrib2 is from [conda-forge](https://anaconda.org/channels/conda-forge/packages/wgrib2/overview).

I recommend installing wgrib2 globally with [Pixi](https://pixi.sh/latest/):

```
pixi global install wgrib2
```

Alternatively, you can install in a conda environment:

```
mamba install wgrib2
```
```
conda install wgrib2
```

# 🐍 Installation

[![Conda](https://img.shields.io/conda/v/conda-forge/herbie-data)](https://anaconda.org/conda-forge/herbie-data)

The easiest way to install Herbie and its dependencies is with [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) from conda-forge.

```bash
conda install -c conda-forge herbie-data
```

## Carpenter Workshop 🧰 (optional)

An _optional_ dependency is my "Carpenter Workshop" package. This has some general tools that are useful for making maps and performing other tasks. You might see me use these tools in the tutorials.

```bash
pip install git+https://github.com/blaylockbk/Carpenter_Workshop.git
```

<br>
<br>
<br>

# pip install

[![PyPI - Version](https://img.shields.io/pypi/v/herbie-data)](https://pypi.org/project/herbie-data/)

Herbie is published on PyPI and you can install it with pip, _but_ it requires some dependencies that you will have to install yourself:

- Python 3.9+
- cURL
- [cfgrib](https://github.com/ecmwf/cfgrib), which requires **_eccodes_**.
- _Optional:_ wgrib2
- _Optional:_ [Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop)

When those are installed within your environment, _then_ you can install Herbie with pip.

```bash
# Install last published version
pip install herbie-data
```

or

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

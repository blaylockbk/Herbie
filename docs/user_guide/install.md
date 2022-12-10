# 🐍 Installation

The easiest way to instal Herbie and its dependencies is with [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) from conda-forge.

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

# Alternative Methods

Herbie is published on PyPI and you can install it with pip, _but_ it requires some dependencies that you will have to install yourself:

- Python 3.8+
- cURL
- [Cartopy](https://scitools.org.uk/cartopy/docs/latest/installing.html), which requires GEOS and Proj.
- [cfgrib](https://github.com/ecmwf/cfgrib), which requires eccodes.
- _Optional:_ wgrib2
- _Optional:_ [Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop)

When those are installed within your environment, _then_ you can install Herbie with pip.

```bash
# Last published version
pip install herbie-data

# ~~ or ~~

# Main Branch
pip install git+https://github.com/blaylockbk/Herbie.git
```



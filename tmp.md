The easiest way to instal Herbie and its dependencies is within a [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) environment. I provided an **[`environment.yml`](https://github.com/blaylockbk/Herbie/blob/main/environment.yml)** file that you may use or modify.

```bash
# Download environment file
wget https://github.com/blaylockbk/Herbie/raw/main/environment.yml

# Create the environment
conda env create -f environment.yml

# Activate the environment
conda activate herbie
```

Alternatively, Herbie is published on PyPI and you can install it with pip, _but_ it requires some dependencies that you will have to install yourself:

- Python 3.8, 3.9, or **3.10** (recommended)
- cURL
- [Cartopy](https://scitools.org.uk/cartopy/docs/latest/installing.html), which requires GEOS and Proj.
- [cfgrib](https://github.com/ecmwf/cfgrib), which requires eccodes.
- _Optional:_ [Carpenter Workshop](https://github.com/blaylockbk/Carpenter_Workshop)
- _Optional:_ wgrib2

When those are installed within your envirment, _then_ you can install Herbie with pip.

```bash
# Latest published version
pip install herbie-data
```

or

```bash
# Most recent changes
pip install git+https://github.com/blaylockbk/Herbie.git
```

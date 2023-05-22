# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# ---- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import pydata_sphinx_theme
from datetime import datetime
import herbie  ## Required to get herbie version and to for accessors to be documented

sys.path.insert(0, os.path.abspath("../.."))

# The full version, including alpha/beta/rc/post tags
release = herbie.__version__

# The version, excluding alpha/beat/rc/tags
version = ".".join([str(i) for i in herbie.__version_tuple__])


# ---- Project information -----------------------------------------------------
utc_now = datetime.utcnow().strftime("%H:%M UTC %d %b %Y")

project = "Herbie"
copyright = f"{datetime.utcnow():%Y}, Brian K. Blaylock.    ♻ Updated: {utc_now}"
author = f"Brian K. Blaylock"


# ---- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "nbsphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "autodocsumm",
    "sphinx_markdown_tables",
    "myst_parser",
    "sphinxcontrib.mermaid",
]

autosummary_generate = True  # Turn on sphinx.ext.autosummary

# MyST Docs: https://myst-parser.readthedocs.io/en/latest/syntax/optional.html
myst_enable_extensions = [
    "linkify",  # Autodetects URL links in Markdown files
]

# Set up mapping for other projects' docs
intersphinx_mapping = {
    "metpy": ("https://unidata.github.io/MetPy/latest/", None),
    "pint": ("https://pint.readthedocs.io/en/stable/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "xarray": ("https://xarray.pydata.org/en/stable/", None),
}

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    ".ipynb_checkpoints",
    ".vscode",
]


# ---- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# Define the json_url for our version switcher.
json_url = "https://pydata-sphinx-theme.readthedocs.io/en/latest/_static/switcher.json"

# Define the version we use for matching in the version switcher.
version_match = os.environ.get("READTHEDOCS_VERSION")
# If READTHEDOCS_VERSION doesn't exist, we're not on RTD
# If it is an integer, we're in a PR build and the version isn't correct.
if not version_match or version_match.isdigit():
    # For local development, infer the version to match from the package.
    release = pydata_sphinx_theme.__version__
    if "dev" in release or "rc" in release:
        version_match = "latest"
        # We want to keep the relative reference if we are in dev mode
        # but we want the whole url if we are effectively in a released version
        json_url = "_static/switcher.json"
    else:
        version_match = release

html_theme_options = {
    "github_url": "https://github.com/blaylockbk/Herbie",
    "twitter_url": "https://twitter.com/blaylockbk",
    "navbar_start": ["navbar-logo"],
    "navbar_center": ["version-switcher", "navbar-nav"],
    "navbar_end": ["theme-switcher", "navbar-icon-links.html", "search-field.html"],
    "switcher": {
        "json_url": json_url,
        "version_match": version_match,
    },
    "use_edit_page_button": True,
    "analytics": {"google_analytics_id": "G-PT9LX1B7B8"},
    "show_toc_level": 1,
    # "switcher": {
    #     "json_url": "https://herbie.readthedocs.io/en/latest/_static/switcher.json",
    #     "version_match": version,
    # },
    "external_links": [
        {
            "name": "SynopticPy",
            "url": "https://synopticpy.readthedocs.io/",
        },
        {
            "name": "GOES-2-go",
            "url": "https://goes2go.readthedocs.io/",
        },
    ],
    "logo": {
        "image_light": "_static/logo_new/Herbie-logo.png",
        "image_dark": "_static/logo_new/Herbie-logo.png",
    },
}

html_sidebars = {}

html_favicon = "_static/logo_new/Herbie-icon.ico"

html_context = {
    "github_user": "blaylockbk",
    "github_repo": "Herbie",
    "github_version": "main",  # Make changes to the main branch
    "doc_path": "docs",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static", "../images"]


fontawesome_included = True
panels_add_bootstrap_css = False  # False, because pydata theme already loads it

html_css_files = ["css/brian_style.css"]

html_js_files = [
    "https://kit.fontawesome.com/f6cc126dcc.js",
]

# Set autodoc defaults
autodoc_default_options = {
    "autosummary": True,  # Include a members "table of contents"
    "members": True,  # Document all functions/members
    "special-members": "__init__",
}

autodoc_mock_imports = [
    "xesmf",
    "numpy",
    "matplotlib",
    "pandas",
    "xarray",
    "cartopy",
    "cfgrib",
    "imageio",
    "siphon",
]

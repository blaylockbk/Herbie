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
from datetime import datetime

import pydata_sphinx_theme

import herbie  # # Required to get herbie version and to for accessors to be documented

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
    "sphinx_copybutton",
    "sphinx.ext.todo",
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
html_favicon = "_static/logo_new/Herbie-icon.ico"

html_theme_options = {
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
    "header_links_before_dropdown": 4,
    "icon_links": [
        {
            "name": "Twitter",
            "url": "https://twitter.com/blaylockbk",
            "icon": "fa-brands fa-twitter",
        },
        {
            "name": "GitHub",
            "url": "https://github.com/blaylockbk/Herbie",
            "icon": "fa-brands fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/herbie-data",
            "icon": "fa-custom fa-pypi",
        },
    ],
    "logo": {
        "image_light": "_static/logo_new/Herbie-logo.png",
        "image_dark": "_static/logo_new/Herbie-logo.png",
    },
    "use_edit_page_button": True,
    "show_toc_level": 1,
    "navbar_align": "left",
    "show_version_warning_banner": True,
    "navbar_center": ["version-switcher", "navbar-nav"],
    "footer_start": ["copyright"],
    "footer_center": ["sphinx-version"],
    "switcher": {
        "json_url": "https://herbie.readthedocs.io/en/latest/_static/switcher.json",
        "version_match": os.environ.get("READTHEDOCS_VERSION"),
    },
}

html_sidebars = {}


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
html_css_files = ["css/brian_style.css"]
html_js_files = []
todo_include_todos = True

# ---- Options for autosummary/autodoc output ---------------------------------

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

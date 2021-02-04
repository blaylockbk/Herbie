# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../'))


# -- Project information -----------------------------------------------------

project = 'HRRR-B'
copyright = '2020, Brian K. Blaylock'
author = 'Brian K. Blaylock'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx_rtd_theme',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.napoleon',
    'recommonmark',
    'autodocsumm',
    'sphinx_markdown_tables'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.txt': 'markdown',
    '.md': 'markdown'
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.ipynb_checkpoints', '.vscode']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'
html_logo = '_static/HRRR-B_logo.png'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', '../images']

html_css_files = [
    'https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css',
]

html_js_files = [
    'https://kit.fontawesome.com/f6cc126dcc.js',
]

# Set autodoc defaults
autodoc_default_options = {
    'autosummary': True,        # Include a members "table of contents"
    'members': True,            # Document all functions/members  
}

autodoc_mock_imports = ["xesmf", "numpy", "matplotlib", "pandas", "xarray", "cartopy", "cfgrib"]


"""
IMPORTANT NOTES ABOUT PUBLISHING TO GITHUB PAGES
-----------------------------------------------
1. Must have an empty file called .nojekell in this directory.

2. Include an index.html file to redirect to the actual html build
   Something like this in that file (yes, only one line)...
        <meta http-equiv="Refresh" content="0;url=_build/html/"/>

3. 
"""

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

import inspect

project = 'Poképy Emulator'
copyright = '2025, Ben Hoskings'
author = 'Ben Hoskings'
release = '0.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

templates_path = ['_templates']
exclude_patterns = []

language = 'english'

autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "includehidden": True,
}

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

def skip_properties(app, what, name, obj, skip, options):
    if what == "class":
        # Skip @property
        if isinstance(obj, property):
            return True
        # Skip data attributes
        if not inspect.isroutine(obj):
            return True
    return skip

def setup(app):
    app.connect("autodoc-skip-member", skip_properties)
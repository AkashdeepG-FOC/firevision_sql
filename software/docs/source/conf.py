import os
import sys

# Add project root to path so autodoc can find the modules
sys.path.insert(0, os.path.abspath('../..'))

project = 'FireVision AI Surveillance System'
copyright = '2026, Developer'
author = 'Developer'
release = '1.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = []

# Options for HTML output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

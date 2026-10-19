# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'MESAWAVE'
copyright = '2026, MESAWAVE'
author = 'MESAWAVE'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'myst_parser',
    'sphinx.ext.napoleon',
    'sphinx_design',
]

myst_enable_extensions = ['colon_fence']
myst_heading_anchors = 2

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'shibuya'
html_title = 'MESAWAVE'
html_theme_options = {
    'accent_color': 'cyan',
    'github_url': 'https://github.com/manishvenu/mesawave',
    'nav_links': [
        {'title': 'Proposal', 'url': 'proposal.pdf', 'resource': True},
    ],
}
html_context = {
    'source_type': 'github',
    'source_user': 'manishvenu',
    'source_repo': 'mesawave',
    'source_version': 'main',
    'source_docs_path': '/docs/source/',
}
# Shibuya's defaults minus the repo-stats box and ads.
html_sidebars = {
    '**': ['sidebars/localtoc.html', 'sidebars/edit-this-page.html'],
}
html_static_path = ['_static']
html_css_files = ['custom.css']
# Copied to the site root, so the proposal lives at /proposal.pdf.
html_extra_path = ['proposal.pdf']

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

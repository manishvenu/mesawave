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
    'sphinxcontrib.mermaid',
]

myst_enable_extensions = ['colon_fence']
myst_heading_anchors = 2

# Short links to the coupling caps, pinned to the versions in CESM_crocodash,
# e.g. [206](ww3:L206) in stream_data_requirements.md.
myst_url_schemes = {
    'http': None,
    'https': None,
    'mailto': None,
    'ww3': 'https://github.com/CROCODILE-CESM/WW3/blob/4b79dba2859ce120adaac00e9ab98ffd12c8b0d5/model/src/wav_import_export.F90#{{path}}',
    'mom6': 'https://github.com/CROCODILE-CESM/MOM6/blob/09d8593619eddfda44cfd6d553e4f8651843654d/config_src/drivers/nuopc_cap/mom_cap.F90#{{path}}',
    'cice': 'https://github.com/ESCOMP/CICE/blob/cice6_6_3_20260904/cicecore/drivers/nuopc/cmeps/ice_import_export.F90#{{path}}',
}

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
html_js_files = ['glossary.js']
# Copied to the site root, so the proposal lives at /proposal.pdf.
html_extra_path = ['proposal.pdf']

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

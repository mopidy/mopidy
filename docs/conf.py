# encoding: utf-8

"""Mopidy documentation build configuration file"""

from __future__ import absolute_import, unicode_literals

import os
import sys


# -- Workarounds to have autodoc generate API docs ----------------------------

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))


class Mock(object):
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        return Mock()

    def __or__(self, other):
        return Mock()

    @classmethod
    def __getattr__(self, name):
        if name == 'get_system_config_dirs':  # GLib.get_system_config_dirs()
            return list
        elif name == 'get_user_config_dir':  # GLib.get_user_config_dir()
            return str
        else:
            return Mock()


MOCK_MODULES = [
    'dbus',
    'dbus.mainloop',
    'dbus.mainloop.glib',
    'dbus.service',
    'mopidy.internal.gi',
]
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()


# -- Custom Sphinx object types -----------------------------------------------

def setup(app):
    from sphinx.ext.autodoc import cut_lines
    app.connect(b'autodoc-process-docstring', cut_lines(4, what=['module']))
    app.add_object_type(
        b'confval', 'confval',
        objname='configuration value',
        indextemplate='pair: %s; configuration value')


# -- General configuration ----------------------------------------------------

needs_sphinx = '1.3'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.extlinks',
    'sphinx.ext.graphviz',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = 'Mopidy'
copyright = '2009-2017, Stein Magnus Jodal and contributors'

from mopidy.internal.versioning import get_version
release = get_version()
version = '.'.join(release.split('.')[:2])

# To make the build reproducible, avoid using today's date in the manpages
today = '2017'

exclude_trees = ['_build']

pygments_style = 'sphinx'

modindex_common_prefix = ['mopidy.']


# -- Options for HTML output --------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

html_use_modindex = True
html_use_index = True
html_split_index = False
html_show_sourcelink = True

htmlhelp_basename = 'Mopidy'


# -- Options for LaTeX output -------------------------------------------------

latex_documents = [
    (
        'index',
        'Mopidy.tex',
        'Mopidy Documentation',
        'Stein Magnus Jodal and contributors',
        'manual'
    ),
]


# -- Options for manpages output ----------------------------------------------

man_pages = [
    (
        'command',
        'mopidy',
        'music server',
        '',
        '1'
    ),
]


# -- Options for extlink extension --------------------------------------------

extlinks = {
    'issue': ('https://github.com/mopidy/mopidy/issues/%s', '#'),
    'commit': ('https://github.com/mopidy/mopidy/commit/%s', 'commit '),
    'js': ('https://github.com/mopidy/mopidy.js/issues/%s', 'mopidy.js#'),
    'mpris': (
        'https://github.com/mopidy/mopidy-mpris/issues/%s', 'mopidy-mpris#'),
    'discuss': ('https://discuss.mopidy.com/t/%s', 'discuss.mopidy.com/t/'),
}


# -- Options for intersphinx extension ----------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/2', None),
    'pykka': ('https://www.pykka.org/en/latest/', None),
    'tornado': ('http://www.tornadoweb.org/en/stable/', None),
}

# -- Options for linkcheck builder -------------------------------------------

linkcheck_ignore = [  # Some sites work in browser but linkcheck fails.
    r'http://localhost:\d+/',
    r'http://wiki.commonjs.org',
    r'http://vk.com',
    r'http://$']

linkcheck_anchors = False  # This breaks on links that use # for other stuff

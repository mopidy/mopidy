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
        if name in ('__file__', '__path__'):
            return '/dev/null'
        elif name == 'get_system_config_dirs':
            # glib.get_system_config_dirs()
            return tuple
        elif name == 'get_user_config_dir':
            # glib.get_user_config_dir()
            return str
        elif (name[0] == name[0].upper() and
                # gst.Caps
                not name.startswith('Caps') and
                # gst.PadTemplate
                not name.startswith('PadTemplate') and
                # dbus.String()
                not name == 'String'):
            return type(name, (), {})
        else:
            return Mock()

MOCK_MODULES = [
    'cherrypy',
    'dbus',
    'dbus.mainloop',
    'dbus.mainloop.glib',
    'dbus.service',
    'glib',
    'gobject',
    'gst',
    'gst.pbutils',
    'pygst',
    'pykka',
    'pykka.actor',
    'pykka.future',
    'pykka.registry',
    'pylast',
    'ws4py',
    'ws4py.messaging',
    'ws4py.server',
    'ws4py.server.cherrypyserver',
    'ws4py.websocket',
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

needs_sphinx = '1.0'

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
copyright = '2009-2015, Stein Magnus Jodal and contributors'

from mopidy.utils.versioning import get_version
release = get_version()
version = '.'.join(release.split('.')[:2])

# To make the build reproducible, avoid using today's date in the manpages
today = '2015'

exclude_trees = ['_build']

pygments_style = 'sphinx'

modindex_common_prefix = ['mopidy.']


# -- Options for HTML output --------------------------------------------------

# 'sphinx_rtd_theme' is bundled with Sphinx 1.3, which we don't have when
# building the docs as part of the Debian packages on e.g. Debian wheezy.
# html_theme = 'sphinx_rtd_theme'
html_theme = 'default'
html_theme_path = ['_themes']
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
    'python': ('http://docs.python.org/2', None),
    'pykka': ('http://www.pykka.org/en/latest/', None),
    'tornado': ('http://www.tornadoweb.org/en/stable/', None),
}

from __future__ import unicode_literals

import os

import mopidy
from mopidy import exceptions, ext
from mopidy.utils import formatting, config


default_config = """
[mpris]
enabled = true
desktop_file = /usr/share/applications/mopidy.desktop
"""

__doc__ = """
Frontend which lets you control Mopidy through the Media Player Remote
Interfacing Specification (`MPRIS <http://www.mpris.org/>`_) D-Bus
interface.

An example of an MPRIS client is the `Ubuntu Sound Menu
<https://wiki.ubuntu.com/SoundMenu>`_.

**Dependencies**

- D-Bus Python bindings. The package is named ``python-dbus`` in
  Ubuntu/Debian.

- ``libindicate`` Python bindings is needed to expose Mopidy in e.g. the
  Ubuntu Sound Menu. The package is named ``python-indicate`` in
  Ubuntu/Debian.

- An ``.desktop`` file for Mopidy installed at the path set in the
  :confval:`mpris/desktop_file` config value. See :ref:`install-desktop-file`
  for details.

**Configuration**

.. confval:: mpris/enabled

    If the MPRIS extension should be enabled or not.

.. confval:: mpris/desktop_file

    Location of the Mopidy ``.desktop`` file.

**Default config**

.. code-block:: ini

%(config)s

**Usage**

The frontend is enabled by default if all dependencies are available.

**Testing the frontend**

To test, start Mopidy, and then run the following in a Python shell::

    import dbus
    bus = dbus.SessionBus()
    player = bus.get_object('org.mpris.MediaPlayer2.mopidy',
        '/org/mpris/MediaPlayer2')

Now you can control Mopidy through the player object. Examples:

- To get some properties from Mopidy, run::

    props = player.GetAll('org.mpris.MediaPlayer2',
        dbus_interface='org.freedesktop.DBus.Properties')

- To quit Mopidy through D-Bus, run::

    player.Quit(dbus_interface='org.mpris.MediaPlayer2')
""" % {'config': formatting.indent(default_config)}


class Extension(ext.Extension):

    dist_name = 'Mopidy-MPRIS'
    ext_name = 'mpris'
    version = mopidy.__version__

    def get_default_config(self):
        return default_config

    def get_config_schema(self):
        schema = config.ExtensionConfigSchema()
        schema['desktop_file'] = config.Path()
        return schema

    def validate_environment(self):
        if 'DISPLAY' not in os.environ:
            raise exceptions.ExtensionError(
                'An X11 $DISPLAY is needed to use D-Bus')

        try:
            import dbus  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('dbus library not found', e)

    def get_frontend_classes(self):
        from .actor import MprisFrontend
        return [MprisFrontend]

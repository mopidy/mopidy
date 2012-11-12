"""
Frontend which lets you control Mopidy through the Media Player Remote
Interfacing Specification (`MPRIS <http://www.mpris.org/>`_) D-Bus
interface.

An example of an MPRIS client is the `Ubuntu Sound Menu
<https://wiki.ubuntu.com/SoundMenu>`_.

**Dependencies:**

- D-Bus Python bindings. The package is named ``python-dbus`` in
  Ubuntu/Debian.

- ``libindicate`` Python bindings is needed to expose Mopidy in e.g. the
  Ubuntu Sound Menu. The package is named ``python-indicate`` in
  Ubuntu/Debian.

- An ``.desktop`` file for Mopidy installed at the path set in
  :attr:`mopidy.settings.DESKTOP_FILE`. See :ref:`install-desktop-file` for
  details.

**Settings:**

- :attr:`mopidy.settings.DESKTOP_FILE`

**Usage:**

Make sure :attr:`mopidy.settings.FRONTENDS` includes
``mopidy.frontends.mpris.MprisFrontend``. By default, the setting includes the
MPRIS frontend.

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
"""

from __future__ import unicode_literals

# flake8: noqa
from .actor import MprisFrontend

**********************
:mod:`mopidy.settings`
**********************


Changing settings
=================

For any Mopidy installation you will need to change at least a couple of
settings. To do this, create a new file in the ``~/.mopidy/`` directory
named ``settings.py`` and add settings you need to change from their defaults
there.

A complete ``~/.mopidy/settings.py`` may look like this::

    SERVER_HOSTNAME = u'0.0.0.0'
    SPOTIFY_USERNAME = u'alice'
    SPOTIFY_USERNAME = u'mysecret'


Available settings
==================

.. automodule:: mopidy.settings
    :synopsis: Available settings and their default values.
    :members:
    :undoc-members:

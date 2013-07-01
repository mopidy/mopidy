.. _ext-scrobbler:

****************
Mopidy-Scrobbler
****************

This extension scrobbles the music you play to your `Last.fm
<http://www.last.fm>`_ profile.

.. note::

    This extension requires a free user account at Last.fm.


Dependencies
============

.. literalinclude:: ../../requirements/scrobbler.txt


Default configuration
=====================

.. literalinclude:: ../../mopidy/frontends/scrobbler/ext.conf
    :language: ini


Configuration values
====================

.. confval:: scrobbler/enabled

    If the scrobbler extension should be enabled or not.

.. confval:: scrobbler/username

    Your Last.fm username.

.. confval:: scrobbler/password

    Your Last.fm password.


Usage
=====

The extension is enabled by default if all dependencies are available. You just
need to add your Last.fm username and password to the
``~/.config/mopidy/mopidy.conf`` file:

.. code-block:: ini

    [scrobbler]
    username = myusername
    password = mysecret

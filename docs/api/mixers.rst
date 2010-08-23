********************
:mod:`mopidy.mixers`
********************

Mixers are responsible for controlling volume. Clients of the mixers will
simply instantiate a mixer and read/write to the ``volume`` attribute::

    >>> from mopidy.mixers.alsa import AlsaMixer
    >>> mixer = AlsaMixer()
    >>> mixer.volume
    100
    >>> mixer.volume = 80
    >>> mixer.volume
    80

Most users will use one of the internal mixers which controls the volume on the
computer running Mopidy. If you do not specify which mixer you want to use in
the settings, Mopidy will choose one for you based upon what OS you run. See
:attr:`mopidy.settings.MIXER` for the defaults.

Mopidy also supports controlling volume on other hardware devices instead of on
the computer running Mopidy through the use of custom mixer implementations. To
enable one of the hardware device mixers, you must the set
:attr:`mopidy.settings.MIXER` setting to point to one of the classes found
below, and possibly add some extra settings required by the mixer you choose.


Mixer API
=========

All mixers should subclass :class:`mopidy.mixers.BaseMixer` and override
methods as described below.

.. automodule:: mopidy.mixers
    :synopsis: Mixer API
    :members:
    :undoc-members:


:mod:`mopidy.mixers.alsa` -- ALSA mixer for Linux
=================================================

.. inheritance-diagram:: mopidy.mixers.alsa

.. automodule:: mopidy.mixers.alsa
    :synopsis: ALSA mixer for Linux
    :members:


:mod:`mopidy.mixers.denon` -- Hardware mixer for Denon amplifiers
=================================================================

.. inheritance-diagram:: mopidy.mixers.denon

.. automodule:: mopidy.mixers.denon
    :synopsis: Hardware mixer for Denon amplifiers
    :members:


:mod:`mopidy.mixers.dummy` -- Dummy mixer for testing
=====================================================

.. inheritance-diagram:: mopidy.mixers.dummy

.. automodule:: mopidy.mixers.dummy
    :synopsis: Dummy mixer for testing
    :members:


:mod:`mopidy.mixers.gstreamer_software` -- Software mixer for all platforms
===========================================================================

.. inheritance-diagram:: mopidy.mixers.gstreamer_software

.. automodule:: mopidy.mixers.gstreamer_software
    :synopsis: Software mixer for all platforms
    :members:


:mod:`mopidy.mixers.osa` -- Osa mixer for OS X
==============================================

.. inheritance-diagram:: mopidy.mixers.osa

.. automodule:: mopidy.mixers.osa
    :synopsis: Osa mixer for OS X
    :members:


:mod:`mopidy.mixers.nad` -- Hardware mixer for NAD amplifiers
=============================================================

.. inheritance-diagram:: mopidy.mixers.nad

.. automodule:: mopidy.mixers.nad
    :synopsis: Hardware mixer for NAD amplifiers
    :members:

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

.. automodule:: mopidy.mixers.alsa
    :synopsis: ALSA mixer for Linux
    :members:

.. inheritance-diagram:: mopidy.mixers.alsa.AlsaMixer


:mod:`mopidy.mixers.denon` -- Hardware mixer for Denon amplifiers
=================================================================

.. automodule:: mopidy.mixers.denon
    :synopsis: Hardware mixer for Denon amplifiers
    :members:

.. inheritance-diagram:: mopidy.mixers.denon


:mod:`mopidy.mixers.dummy` -- Dummy mixer for testing
=====================================================

.. automodule:: mopidy.mixers.dummy
    :synopsis: Dummy mixer for testing
    :members:

.. inheritance-diagram:: mopidy.mixers.dummy


:mod:`mopidy.mixers.osa` -- Osa mixer for OS X
==============================================

.. automodule:: mopidy.mixers.osa
    :synopsis: Osa mixer for OS X
    :members:

.. inheritance-diagram:: mopidy.mixers.osa


:mod:`mopidy.mixers.nad` -- Hardware mixer for NAD amplifiers
=============================================================

.. automodule:: mopidy.mixers.nad
    :synopsis: Hardware mixer for NAD amplifiers
    :members:

.. inheritance-diagram:: mopidy.mixers.nad

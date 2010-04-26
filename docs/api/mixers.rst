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


Mixer API
=========

All mixers should subclass :class:`mopidy.mixers.BaseMixer` and override
methods as described below.

.. automodule:: mopidy.mixers
    :synopsis: Sound mixer interface.
    :members:
    :undoc-members:


Internal mixers
===============

Most users will use one of these internal mixers which controls the volume on
the computer running Mopidy. If you do not specify which mixer you want to use
in the settings, Mopidy will choose one for you based upon what OS you run. See
:attr:`mopidy.settings.MIXER` for the defaults.


:mod:`mopidy.mixers.alsa` -- ALSA mixer
---------------------------------------

.. automodule:: mopidy.mixers.alsa
    :synopsis: ALSA mixer for Linux.
    :members:

.. inheritance-diagram:: mopidy.mixers.alsa.AlsaMixer


:mod:`mopidy.mixers.dummy` -- Dummy mixer
-----------------------------------------

.. automodule:: mopidy.mixers.dummy
    :synopsis: Dummy mixer for testing.
    :members:

.. inheritance-diagram:: mopidy.mixers.dummy


:mod:`mopidy.mixers.osa` -- Osa mixer
-------------------------------------

.. automodule:: mopidy.mixers.osa
    :synopsis: Osa mixer for OS X.
    :members:

.. inheritance-diagram:: mopidy.mixers.osa


External device mixers
======================

Mopidy supports controlling volume on external devices instead of on the
computer running Mopidy through the use of custom mixer implementations. To
enable one of the following mixers, you must the set
:attr:`mopidy.settings.MIXER` setting to point to one of the classes
found below, and possibly add some extra settings required by the mixer you
choose.


:mod:`mopidy.mixers.denon` -- Denon amplifier mixer
---------------------------------------------------

.. automodule:: mopidy.mixers.denon
    :synopsis: Denon amplifier mixer.
    :members:

.. inheritance-diagram:: mopidy.mixers.denon


:mod:`mopidy.mixers.nad` -- NAD amplifier mixer
-----------------------------------------------

.. automodule:: mopidy.mixers.nad
    :synopsis: NAD amplifier mixer.
    :members:

.. inheritance-diagram:: mopidy.mixers.nad

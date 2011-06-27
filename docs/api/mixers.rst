*********
Mixer API
*********

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

All mixers should subclass :class:`mopidy.mixers.base.BaseMixer` and override
methods as described below.

.. automodule:: mopidy.mixers.base
    :synopsis: Mixer API
    :members:


Mixer implementations
=====================

* :mod:`mopidy.mixers.alsa`
* :mod:`mopidy.mixers.denon`
* :mod:`mopidy.mixers.dummy`
* :mod:`mopidy.mixers.gstreamer_software`
* :mod:`mopidy.mixers.osa`
* :mod:`mopidy.mixers.nad`

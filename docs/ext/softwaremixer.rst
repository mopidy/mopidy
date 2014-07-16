.. _ext-softwaremixer:

********************
Mopidy-SoftwareMixer
********************

Mopidy-SoftwareMixer is an extension for controlling audio volume in software
through GStreamer. It is the only mixer bundled with Mopidy and is enabled by
default.

If you use PulseAudio, the software mixer will control the per-application
volume for Mopidy in PulseAudio, and any changes to the per-application volume
done from outside Mopidy will be reflected by the software mixer.

If you don't use PulseAudio, the mixer will adjust the volume internally in
Mopidy's GStreamer pipeline.


Configuration
=============

Multiple mixers can be installed and enabled at the same time, but only the
mixer pointed to by the :confval:`audio/mixer` config value will actually be
used.

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/softwaremixer/ext.conf
    :language: ini

.. confval:: softwaremixer/enabled

    If the software mixer should be enabled or not. Usually you don't want to
    change this, but instead change the :confval:`audio/mixer` config value to
    decide which mixer is actually used.

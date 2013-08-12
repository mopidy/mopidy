"""Mixer element that automatically selects the real mixer to use.

This is Mopidy's default mixer.

If this wasn't the default, you would set the :confval:`audio/mixer` config
value to ``autoaudiomixer`` to use this mixer.
"""

from __future__ import unicode_literals

import pygst
pygst.require('0.10')
import gst

import logging

logger = logging.getLogger('mopidy.audio.mixers.auto')


# TODO: we might want to add some ranking to the mixers we know about?
class AutoAudioMixer(gst.Bin):
    __gstdetails__ = (
        'AutoAudioMixer',
        'Mixer',
        'Element automatically selects a mixer.',
        'Mopidy')

    def __init__(self):
        gst.Bin.__init__(self)
        mixer = self._find_mixer()
        if mixer:
            self.add(mixer)
            logger.debug('AutoAudioMixer chose: %s', mixer.get_name())
        else:
            logger.debug('AutoAudioMixer did not find any usable mixers')

    def _find_mixer(self):
        registry = gst.registry_get_default()

        factories = registry.get_feature_list(gst.TYPE_ELEMENT_FACTORY)
        factories.sort(key=lambda f: (-f.get_rank(), f.get_name()))

        for factory in factories:
            # Avoid sink/srcs that implement mixing.
            if factory.get_klass() != 'Generic/Audio':
                continue
            # Avoid anything that doesn't implement mixing.
            elif not factory.has_interface('GstMixer'):
                continue

            if self._test_mixer(factory):
                return factory.create()

        return None

    def _test_mixer(self, factory):
        element = factory.create()
        if not element:
            return False

        try:
            result = element.set_state(gst.STATE_READY)
            if result != gst.STATE_CHANGE_SUCCESS:
                return False

            # Trust that the default device is sane and just check tracks.
            return self._test_tracks(element)
        finally:
            element.set_state(gst.STATE_NULL)

    def _test_tracks(self, element):
        # Only allow elements that have a least one output track.
        flags = gst.interfaces.MIXER_TRACK_OUTPUT

        for track in element.list_tracks():
            if track.flags & flags:
                return True
        return False

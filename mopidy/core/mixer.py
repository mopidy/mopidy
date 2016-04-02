from __future__ import absolute_import, unicode_literals

import contextlib
import logging

from mopidy import exceptions
from mopidy.internal import validation
from mopidy.internal.models import MixerState


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _mixer_error_handling(mixer):
    try:
        yield
    except exceptions.ValidationError as e:
        logger.error('%s mixer returned bad data: %s',
                     mixer.actor_ref.actor_class.__name__, e)
    except Exception:
        logger.exception('%s mixer caused an exception.',
                         mixer.actor_ref.actor_class.__name__)


class MixerController(object):
    pykka_traversable = True

    def __init__(self, mixer):
        self._mixer = mixer

    def get_volume(self):
        """Get the volume.

        Integer in range [0..100] or :class:`None` if unknown.

        The volume scale is linear.
        """
        if self._mixer is None:
            return None

        with _mixer_error_handling(self._mixer):
            volume = self._mixer.get_volume().get()
            volume is None or validation.check_integer(volume, min=0, max=100)
            return volume

        return None

    def set_volume(self, volume):
        """Set the volume.

        The volume is defined as an integer in range [0..100].

        The volume scale is linear.

        Returns :class:`True` if call is successful, otherwise :class:`False`.
        """
        validation.check_integer(volume, min=0, max=100)

        if self._mixer is None:
            return False  # TODO: 2.0 return None

        with _mixer_error_handling(self._mixer):
            result = self._mixer.set_volume(volume).get()
            validation.check_instance(result, bool)
            return result

        return False

    def get_mute(self):
        """Get mute state.

        :class:`True` if muted, :class:`False` unmuted, :class:`None` if
        unknown.
        """
        if self._mixer is None:
            return None

        with _mixer_error_handling(self._mixer):
            mute = self._mixer.get_mute().get()
            mute is None or validation.check_instance(mute, bool)
            return mute

        return None

    def set_mute(self, mute):
        """Set mute state.

        :class:`True` to mute, :class:`False` to unmute.

        Returns :class:`True` if call is successful, otherwise :class:`False`.
        """
        validation.check_boolean(mute)
        if self._mixer is None:
            return False  # TODO: 2.0 return None

        with _mixer_error_handling(self._mixer):
            result = self._mixer.set_mute(bool(mute)).get()
            validation.check_instance(result, bool)
            return result

        return False

    def _save_state(self):
        return MixerState(volume=self.get_volume(),
                          mute=self.get_mute())

    def _load_state(self, state, coverage):
        if state and 'mixer' in coverage:
            self.set_mute(state.mute)
            if state.volume:
                self.set_volume(state.volume)

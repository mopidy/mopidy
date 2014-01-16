from __future__ import unicode_literals

import logging

import gobject
import pykka

logger = logging.getLogger(__name__)


def send_async(cls, event, **kwargs):
    gobject.idle_add(lambda: send(cls, event, **kwargs))


def send(cls, event, **kwargs):
    listeners = pykka.ActorRegistry.get_by_class(cls)
    logger.debug('Sending %s to %s: %s', event, cls.__name__, kwargs)
    for listener in listeners:
        listener.proxy().on_event(event, **kwargs)


class Listener(object):
    def on_event(self, event, **kwargs):
        """
        Called on all events.

        *MAY* be implemented by actor. By default, this method forwards the
        event to the specific event methods.

        :param event: the event name
        :type event: string
        :param kwargs: any other arguments to the specific event handlers
        """
        getattr(self, event)(**kwargs)

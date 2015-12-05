from __future__ import absolute_import, unicode_literals

import logging

import pykka

logger = logging.getLogger(__name__)


def send(cls, event, **kwargs):
    listeners = pykka.ActorRegistry.get_by_class(cls)
    logger.debug('Sending %s to %s: %s', event, cls.__name__, kwargs)
    for listener in listeners:
        # Save time by calling methods on Pykka actor without creating a
        # throwaway actor proxy.
        #
        # Because we use `.tell()` there is no return channel for any errors,
        # so Pykka logs them immediately. The alternative would be to use
        # `.ask()` and `.get()` the returned futures to block for the listeners
        # to react and return their exceptions to us. Since emitting events in
        # practise is making calls upwards in the stack, blocking here would
        # quickly deadlock.
        listener.tell({
            'command': 'pykka_call',
            'attr_path': ('on_event',),
            'args': (event,),
            'kwargs': kwargs,
        })


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
        try:
            getattr(self, event)(**kwargs)
        except Exception:
            # Ensure we don't crash the actor due to "bad" events.
            logger.exception(
                'Triggering event failed: %s(%s)', event, ', '.join(kwargs))

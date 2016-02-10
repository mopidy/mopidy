from __future__ import absolute_import, unicode_literals

import logging
import threading

import pykka

from mopidy.compat import thread


logger = logging.getLogger(__name__)


def exit_process():
    logger.debug('Interrupting main...')
    thread.interrupt_main()
    logger.debug('Interrupted main')


def sigterm_handler(signum, frame):
    """A :mod:`signal` handler which will exit the program on signal.

    This function is not called when the process' main thread is running a GLib
    mainloop. In that case, the GLib mainloop must listen for SIGTERM signals
    and quit itself.

    For Mopidy subcommands that does not run the GLib mainloop, this handler
    ensures a proper shutdown of the process on SIGTERM.
    """
    logger.info('Got SIGTERM signal. Exiting...')
    exit_process()


def stop_actors_by_class(klass):
    actors = pykka.ActorRegistry.get_by_class(klass)
    logger.debug('Stopping %d instance(s) of %s', len(actors), klass.__name__)
    for actor in actors:
        actor.stop()


def stop_remaining_actors():
    num_actors = len(pykka.ActorRegistry.get_all())
    while num_actors:
        logger.error(
            'There are actor threads still running, this is probably a bug')
        logger.debug(
            'Seeing %d actor and %d non-actor thread(s): %s',
            num_actors, threading.active_count() - num_actors,
            ', '.join([t.name for t in threading.enumerate()]))
        logger.debug('Stopping %d actor(s)...', num_actors)
        pykka.ActorRegistry.stop_all()
        num_actors = len(pykka.ActorRegistry.get_all())
    logger.debug('All actors stopped.')

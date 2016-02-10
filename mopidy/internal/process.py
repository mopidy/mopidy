from __future__ import absolute_import, unicode_literals

import logging
import os
import signal
import threading

import pykka


logger = logging.getLogger(__name__)


SIGNALS = dict(
    (k, v) for v, k in signal.__dict__.items()
    if v.startswith('SIG') and not v.startswith('SIG_'))


def exit_process():
    logger.debug('Interrupting main...')
    os.kill(os.getpid(), signal.SIGINT)
    logger.debug('Interrupted main')


def exit_handler(signum, frame):
    """A :mod:`signal` handler which will exit the program on signal."""
    logger.info('Got %s signal', SIGNALS[signum])
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

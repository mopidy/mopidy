"""
The WebSockets frontend.
based on mpd-frontend and examples from gevent-socketio
"""

import datetime as dt
import logging
import os
import sys

from mopidy.frontends.ws import exceptions

from pykka import registry, actor

from mopidy import listeners, settings
from mopidy.utils import network, process, log

from mopidy.backends.base import Backend
from mopidy.mixers.base import BaseMixer
from mopidy.listeners import BackendListener
from mopidy.backends.base import PlaybackController
from mopidy.models import Playlist

#get directory with static web content
webdir = os.path.join(os.path.dirname(__file__), 'web')
logger = logging.getLogger('mopidy.frontends.ws')
srv = None

class WsFrontend(actor.ThreadingActor, listeners.BackendListener):
    """
    The WebSockets frontend.

    **Dependencies:**

    - gevent-socketio

    **Settings:**

    - :attr:`mopidy.settings.WS_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.WS_SERVER_PORT`
    """
 
    def on_start(self):
        from mopidy.frontends.ws import wsserver

        global srv
        hostname = network.format_hostname(settings.WS_SERVER_HOSTNAME)
        port = settings.WS_SERVER_PORT
        
        try:
            srv = wsserver.IOServer()
            srv.start(hostname, port)
            
            logger.info(u'Websockets server running at [%s]:%s and on port 10843 (flash policy server)', hostname, port)
        except IOError, e:
            logger.error(u'Websockets server startup failed: %s', e)
            sys.exit(1)

    def on_stop(self):
        from mopidy.frontends.ws import wsserver
        logger.info('stop ws')
        process.stop_actors_by_class(IOServer)
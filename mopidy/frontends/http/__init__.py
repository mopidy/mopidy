"""
Frontend which lets you control Mopidy through HTTP and WebSockets.

**Dependencies**

- ``cherrypy``

- ``ws4py``

**Settings**

- :attr:`mopidy.settings.HTTP_SERVER_HOSTNAME`

- :attr:`mopidy.settings.HTTP_SERVER_PORT`

**Usage**

When this frontend is included in :attr:`mopidy.settings.FRONTENDS`, it starts
a web server at the port specified by :attr:`mopidy.settings.HTTP_SERVER_PORT`.
This web server exposes both a REST web service at the URL ``/api``, and a
WebSocket at ``/ws``.

The REST API gives you access to most Mopidy functionality, while the WebSocket
enables Mopidy to instantly push events to the client, as they happen.

It is also the intention that the frontend should be able to host static files
for any external JavaScript client. This has currently not been implemented.

**API stability**

This frontend is currently to be regarded as **experimental**, and we are not
promising to keep any form of backwards compatibility between releases.
"""

# flake8: noqa
from .actor import HttpFrontend

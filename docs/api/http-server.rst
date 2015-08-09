.. _http-server-api:

********************
HTTP server side API
********************

The :ref:`ext-http` extension comes with an HTTP server to host Mopidy's
:ref:`http-api`. This web server can also be used by other extensions that need
to expose something over HTTP.

The HTTP server side API can be used to:

- host static files for e.g. a Mopidy client written in pure JavaScript,
- host a `Tornado <http://www.tornadoweb.org/>`__ application, or
- host a WSGI application, including e.g. Flask applications.

To host static files using the web server, an extension needs to register a
name and a file path in the extension registry under the ``http:static`` key.

To extend the web server with a web application, an extension must register a
name and a factory function in the extension registry under the ``http:app``
key.

For details on how to make a Mopidy extension, see the :ref:`extensiondev`
guide.


.. _static-web-client:

Static web client example
=========================

To serve static files, you just need to register an ``http:static`` dictionary
in the extension registry. The dictionary must have two keys: ``name`` and
``path``. The ``name`` is used to build the URL the static files will be
served on. By convention, it should be identical with the extension's
:attr:`~mopidy.ext.Extension.ext_name`, like in the following example. The
``path`` tells Mopidy where on the disk the static files are located.

Assuming that the code below is located in the file
:file:`mywebclient/__init__.py`, the files in the directory
:file:`mywebclient/static/` will be made available at ``/mywebclient/`` on
Mopidy's web server. For example, :file:`mywebclient/static/foo.html` will be
available at http://localhost:6680/mywebclient/foo.html.

::

    from __future__ import absolute_import, unicode_literals

    import os

    from mopidy import ext


    class MyWebClientExtension(ext.Extension):
        ext_name = 'mywebclient'

        def setup(self, registry):
            registry.add('http:static', {
                'name': self.ext_name,
                'path': os.path.join(os.path.dirname(__file__), 'static'),
            })

        # See the Extension API for the full details on this class


Tornado application example
===========================

The :ref:`ext-http` extension's web server is based on the `Tornado
<http://www.tornadoweb.org/>`__ web framework. Thus, it has first class support
for Tornado request handlers.

In the following example, we create a :class:`tornado.web.RequestHandler`
called :class:`MyRequestHandler` that responds to HTTP GET requests with the
string ``Hello, world! This is Mopidy $version``, where it gets the Mopidy
version from Mopidy's core API.

To hook the request handler into Mopidy's web server, we must register a
dictionary under the ``http:app`` key in the extension registry. The
dictionary must have two keys: ``name`` and ``factory``.

The ``name`` is used to build the URL the app will be served on. By convention,
it should be identical with the extension's
:attr:`~mopidy.ext.Extension.ext_name`, like in the following example.

The ``factory`` must be a function that accepts two arguments, ``config`` and
``core``, respectively a dict structure of Mopidy's config and a
:class:`pykka.ActorProxy` to the full Mopidy core API. The ``factory`` function
must return a list of Tornado request handlers. The URL patterns of the request
handlers should not include the ``name``, as that will be prepended to the URL
patterns by the web server.

When the extension is installed, Mopidy will respond to requests to
http://localhost:6680/mywebclient/ with the string ``Hello, world! This is
Mopidy $version``.

::

    from __future__ import absolute_import, unicode_literals

    import os

    import tornado.web

    from mopidy import ext


    class MyRequestHandler(tornado.web.RequestHandler):
        def initialize(self, core):
            self.core = core

        def get(self):
            self.write(
                'Hello, world! This is Mopidy %s' %
                self.core.get_version().get())


    def my_app_factory(config, core):
        return [
            ('/', MyRequestHandler, {'core': core})
        ]


    class MyWebClientExtension(ext.Extension):
        ext_name = 'mywebclient'

        def setup(self, registry):
            registry.add('http:app', {
                'name': self.ext_name,
                'factory': my_app_factory,
            })

        # See the Extension API for the full details on this class



WSGI application example
========================

WSGI applications are second-class citizens on Mopidy's HTTP server. The WSGI
applications are run inside Tornado, which is based on non-blocking I/O and a
single event loop. In other words, your WSGI applications will only have a
single thread to run on, and if your application is doing blocking I/O, it will
block all other requests from being handled by the web server as well.

The example below shows how a WSGI application that returns the string
``Hello, world! This is Mopidy $version`` on all requests. The WSGI application
is wrapped as a Tornado application and mounted at
http://localhost:6680/mywebclient/.

::

    from __future__ import absolute_import, unicode_literals

    import os

    import tornado.web
    import tornado.wsgi

    from mopidy import ext


    def my_app_factory(config, core):

        def wsgi_app(environ, start_response):
            status = '200 OK'
            response_headers = [('Content-type', 'text/plain')]
            start_response(status, response_headers)
            return [
                'Hello, world! This is Mopidy %s\n' %
                self.core.get_version().get()
            ]

        return [
            ('(.*)', tornado.web.FallbackHandler, {
                'fallback': tornado.wsgi.WSGIContainer(wsgi_app),
            }),
        ]


    class MyWebClientExtension(ext.Extension):
        ext_name = 'mywebclient'

        def setup(self, registry):
            registry.add('http:app', {
                'name': self.ext_name,
                'factory': my_app_factory,
            })

        # See the Extension API for the full details on this class


API implementors
================

See :ref:`ext-web`.

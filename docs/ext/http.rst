.. _ext-http:

***********
Mopidy-HTTP
***********

Mopidy-HTTP is an extension that lets you control Mopidy through HTTP and
WebSockets, for example from a web client. It is bundled with Mopidy and
enabled by default.

When it is enabled it starts a web server at the port specified by the
:confval:`http/port` config value.

.. warning::

    As a simple security measure, the web server is by default only available
    from localhost. To make it available from other computers, change the
    :confval:`http/hostname` config value. Before you do so, note that the HTTP
    extension does not feature any form of user authentication or
    authorization. Anyone able to access the web server can use the full core
    API of Mopidy. Thus, you probably only want to make the web server
    available from your local network or place it behind a web proxy which
    takes care or user authentication. You have been warned.


Using a web based Mopidy client
===============================

Mopidy-HTTP's web server can also host any static files, for example the HTML,
CSS, JavaScript, and images needed for a web based Mopidy client. To host
static files, change the :confval:`http/static_dir` config value to point to
the root directory of your web client, for example::

    [http]
    static_dir = /home/alice/dev/the-client

If the directory includes a file named ``index.html``, it will be served on the
root of Mopidy's web server.

If you're making a web based client and wants to do server side development as
well, you are of course free to run your own web server and just use Mopidy's
web server to host the API end points. But, for clients implemented purely in
JavaScript, letting Mopidy host the files is a simpler solution.

See :ref:`http-api` for details on how to integrate with Mopidy over HTTP. If
you're looking for a web based client for Mopidy, go check out
:ref:`http-clients`.


Extending the server's functionality
====================================

If you wish to extend the server with additional server side functionality you
must create class that implements the :class:`mopidy.http.Router` interface and
install it in the extension registry under the ``http:router`` name.

The default implementation of :class:`mopidy.http.Router` already supports
serving static files. If you just want to serve static files you only need to
define the class variables :attr:`mopidy.http.Router.name` and
:attr:`mopidy.http.Router.path`. For example::

    class MyWebClient(http.Router):
        name = 'mywebclient'
        path = os.path.join(os.path.dirname(__file__), 'public_html')

If you wish to extend server with custom methods you can override the method
:meth:`mopidy.http.Router.setup_routes` and define custom routes.


Configuration
=============

See :ref:`config` for general help on configuring Mopidy.

.. literalinclude:: ../../mopidy/http/ext.conf
    :language: ini

.. confval:: http/enabled

    If the HTTP extension should be enabled or not.

.. confval:: http/hostname

    Which address the HTTP server should bind to.

    ``127.0.0.1``
        Listens only on the IPv4 loopback interface
    ``::1``
        Listens only on the IPv6 loopback interface
    ``0.0.0.0``
        Listens on all IPv4 interfaces
    ``::``
        Listens on all interfaces, both IPv4 and IPv6

.. confval:: http/port

    Which TCP port the HTTP server should listen to.

.. confval:: http/static_dir

    Which directory the HTTP server should serve at "/"

    Change this to have Mopidy serve e.g. files for your JavaScript client.
    "/mopidy" will continue to work as usual even if you change this setting.

.. confval:: http/zeroconf

    Name of the HTTP service when published through Zeroconf. The variables
    ``$hostname`` and ``$port`` can be used in the name.

    If set, the Zeroconf services ``_http._tcp`` and ``_mopidy-http._tcp`` will
    be published.

    Set to an empty string to disable Zeroconf for HTTP.

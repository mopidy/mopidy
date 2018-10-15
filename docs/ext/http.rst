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
    takes care of user authentication. You have been warned.


Hosting web clients
===================

Mopidy-HTTP's web server can also host Tornado apps or any static files, for
example the HTML, CSS, JavaScript, and images needed for a web based Mopidy
client. See :ref:`http-server-api` for how to make static files or server-side
functionality from a Mopidy extension available through Mopidy's web server.

If you're making a web based client and want to do server side development
using some other technology than Tornado, you are of course free to run your
own web server and just use Mopidy's web server to host the API endpoints.
But, for clients implemented purely in JavaScript, letting Mopidy host the
files is a simpler solution.

See :ref:`http-api` for details on how to integrate with Mopidy over HTTP. If
you're looking for a web based client for Mopidy, go check out
:ref:`http-clients`.


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

    **Deprecated:** This config is deprecated and will be removed in a future
    version of Mopidy.

    Which directory the HTTP server should serve at "/"

    Change this to have Mopidy serve e.g. files for your JavaScript client.
    "/mopidy" will continue to work as usual even if you change this setting,
    but any other Mopidy webclient installed with pip to be served at
    "/ext_name" will stop working if you set this config.

    You're strongly encouraged to make Mopidy extensions which use the the
    :ref:`http-server-api` to host static files on Mopidy's web server instead
    of using :confval:`http/static_dir`. That way, installation of your web
    client will be a lot easier for your end users, and multiple web clients
    can easily share the same web server.

.. confval:: http/zeroconf

    Name of the HTTP service when published through Zeroconf. The variables
    ``$hostname`` and ``$port`` can be used in the name.

    If set, the Zeroconf services ``_http._tcp`` and ``_mopidy-http._tcp`` will
    be published.

    Set to an empty string to disable Zeroconf for HTTP.

.. confval:: http/allowed_origins

    A list of domains allowed to perform Cross-Origin Resource Sharing (CORS)
    requests. This applies to both JSON-RPC and WebSocket requests. Values
    should be in the format ``hostname:port`` and separated by either a comma or
    newline.
    
    Same-origin requests (i.e. requests from Mopidy's web server) are always
    allowed and so you don't need an entry for those. However, if your requests
    originate from a different web server, you will need to add an entry for
    that server in this list.

.. confval:: http/csrf_protection

    Enable the HTTP server's protection against Cross-Site Request Forgery
    (CSRF) from both JSON-RPC and WebSocket requests.

    Disabling this will remove the requirement to set a ``Content-Type: application/json``
    header for JSON-RPC POST requests. It will also disable all same-origin
    checks, effectively ignoring the :confval:`http/allowed_origins` config
    since requests from any origin will be allowed. Lastly, all
    ``Access-Control-Allow-*`` response headers will be suppressed.

    This config should only be disabled if you understand the security implications
    and require the HTTP server's old behaviour.

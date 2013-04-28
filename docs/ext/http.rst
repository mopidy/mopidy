.. _ext-http:

***********
Mopidy-HTTP
***********

The HTTP extension lets you control Mopidy through HTTP and WebSockets, e.g.
from a web based client. See :ref:`http-api` for details on how to integrate
with Mopidy over HTTP.


Known issues
============

https://github.com/mopidy/mopidy/issues?labels=HTTP+frontend


Dependencies
============

.. literalinclude:: ../../requirements/http.txt


Default configuration
=====================

.. literalinclude:: ../../mopidy/frontends/http/ext.conf
    :language: ini


Configuration values
====================

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


Usage
=====

The extension is enabled by default if all dependencies are available.

When it is enabled it starts a web server at the port specified by the
:confval:`http/port` config value.

.. warning:: Security

    As a simple security measure, the web server is by default only available
    from localhost. To make it available from other computers, change the
    :confval:`http/hostname` config value. Before you do so, note that the HTTP
    extension does not feature any form of user authentication or
    authorization. Anyone able to access the web server can use the full core
    API of Mopidy. Thus, you probably only want to make the web server
    available from your local network or place it behind a web proxy which
    takes care or user authentication. You have been warned.


Using a web based Mopidy client
-------------------------------

The web server can also host any static files, for example the HTML, CSS,
JavaScript, and images needed for a web based Mopidy client. To host static
files, change the ``http/static_dir`` to point to the root directory of your
web client, e.g.::

    [http]
    static_dir = /home/alice/dev/the-client

If the directory includes a file named ``index.html``, it will be served on the
root of Mopidy's web server.

If you're making a web based client and wants to do server side development as
well, you are of course free to run your own web server and just use Mopidy's
web server for the APIs. But, for clients implemented purely in JavaScript,
letting Mopidy host the files is a simpler solution.

If you're looking for a web based client for Mopidy, go check out
:ref:`http-clients`.

.. _extensiondev:

*********************
Extension development
*********************

Mopidy started as simply an MPD server that could play music from Spotify.
Early on, Mopidy got multiple "frontends" to expose Mopidy to more than just MPD
clients, including:

- the scrobbler frontend that scrobbles your listening history to your Last.fm
  account,
- the MPRIS frontend that integrates Mopidy into the Ubuntu Sound Menu, and
- the HTTP server and JavaScript player API making web based Mopidy clients
  possible.

In Mopidy 0.9 we added support for multiple music sources without stopping and
reconfiguring Mopidy, introducing:

- the local backend for playing music from your disk,
- the stream backend for playing Internet radio streams, and
- the Spotify and SoundCloud backends, for playing music directly from those
  services.

All of these are examples of what you can accomplish by creating a Mopidy
extension.

If you want to create your own Mopidy extension for something that does not
exist yet, this guide to extension development will help you get your extension
running in no time, and make it feel the way users would expect your extension
to behave.


Extension project template
==========================

We've made a `Copier <https://copier.readthedocs.io/>`_ project template for
`creating new Mopidy extensions
<https://github.com/mopidy/mopidy-ext-template>`_.

By running a single command,
you're asked a few questions about the name of your extension, and then your
answers are used to create a folder structure similar to the above, with all the
needed files and most of the details filled in for you.

See the readme of `mopidy-ext-template
<https://github.com/mopidy/mopidy-ext-template>`_ for further details.


Anatomy of an extension
=======================

Extensions are located in a Python package called ``mopidy_something`` where
"something" is the name of the application, library or web service you want to
integrate with Mopidy. So, for example, if you plan to add support for a service
named Soundspot to Mopidy, you would name your extension's Python package
``mopidy_soundspot``.

The extension must be registered on `PyPI <https://pypi.org/>`_. The name of the
distribution on PyPI would be something like "mopidy-soundspot". This is the
name users will use when they install your extension from PyPI.

Mopidy extensions must be licensed under an Apache 2.0 (like Mopidy itself),
BSD, MIT or more liberal license to be able to be enlisted in the Mopidy
documentation. The license text should be included in the ``LICENSE`` file in
the root of the extension's Git repo.

Combining this together, we get the following folder structure for our
extension, Mopidy-Soundspot::

    mopidy-soundspot/           # The Git repo root
        pyproject.toml          # Project metadata and build configuration
        LICENSE                 # The license text
        README.md               # Document what it is and how to use it
        src/
            mopidy_soundspot/   # Your code
                __init__.py
                ext.conf        # Default config for the extension
                ...
        tests/
            __init__.py
            test_extension.py   # Tests for the extension

See the above project template for examples of each of the files.


Extension registration
======================

For Mopidy to find your extension, the extension must register an `entry point
<https://packaging.python.org/en/latest/specifications/entry-points/>`_ of the
``mopidy.ext`` type.

This is done by adding a section like this to your
``pyproject.toml`` file:

.. code-block:: toml

    [project.entry-points."mopidy.ext"]
    soundspot = "mopidy_soundspot:Extension"

In this example, the first part, ``soundspot``, is your extensions "short name",
which is used to identify your extension in the Mopidy configuration file. The
second part, ``mopidy_soundspot:Extension``, is the fully qualified name of your
Python module and extension class.


Extension class
===============

The root of your Python package should have a class named ``Extension`` which
inherits from Mopidy's extension base class, :class:`mopidy.ext.Extension`. This
is the class referred to in the ``project.entry-points`` part of
``pyproject.toml``.

Any imports of other files in your extension, outside of Mopidy and its core
requirements, should be kept inside methods. This ensures that this file can be
imported without raising :exc:`ImportError` exceptions for missing dependencies,
etc.

The default configuration for the extension is defined by the
``get_default_config()`` method in the ``Extension`` class which returns a
:mod:`ConfigParser` compatible config section. The config section's name must be
the same as the extension's short name, as defined in the
```project.entry-points`` part of ``pyproject.toml``, for example ``soundspot``.

All extensions must include an ``enabled`` config which normally should default
to ``true``.

Provide good defaults for all config values so that as few users as possible
will need to change them. The exception is if the config value has security
implications; in that case you should default to the most secure configuration.

Leave any configurations that don't have meaningful defaults blank, like
``username`` and ``password``. In the example below, we've chosen to maintain
the default config as a separate file named ``ext.conf``. This makes it easy to
include the default config in documentation without duplicating it.

This is ``src/mopidy_soundspot/__init__.py``::

    import logging
    import pathlib
    from importlib.metadata import version

    from mopidy import config, exceptions, ext

    __version__ = version('mopidy-soundspot')

    # If you need to log, use loggers named after the current Python module
    logger = logging.getLogger(__name__)


    class Extension(ext.Extension):
        dist_name = "Mopidy-Soundspot"
        ext_name = "soundspot"
        version = __version__

        def get_default_config(self):
            return config.read(pathlib.Path(__file__).parent / "ext.conf")

        def get_config_schema(self):
            schema = super().get_config_schema()
            schema["username"] = config.String()
            schema["password"] = config.Secret()
            return schema

        def get_command(self):
            # To extend the `mopidy` command line interface:
            from .commands import SoundspotCommand
            return SoundspotCommand()

        def validate_environment(self):
            # Any manual checks of the environment to fail early.
            # Dependencies described by pyproject.toml are checked by Mopidy, so
            # you should not check their presence here.
            pass

        def setup(self, registry):
            # You will typically only do one of the following things in a
            # single extension.

            # Register a frontend
            from .frontend import SoundspotFrontend
            registry.add('frontend', SoundspotFrontend)

            # Register a backend
            from .backend import SoundspotBackend
            registry.add('backend', SoundspotBackend)

            # Or nothing to register e.g. command extension
            pass

And this is ``src/mopidy_soundspot/ext.conf``:

.. code-block:: ini

    [soundspot]
    enabled = true
    username =
    password =

For more detailed documentation on the extension class, see the :ref:`ext-api`.


Example frontend
================

If you want to *use* Mopidy's core API from your extension, then you want to
implement a frontend.

The skeleton of a frontend would look like this. Notice that the frontend gets
passed a reference to the core API when it's created. See the
:ref:`frontend-api` for more details.

::

    import pykka

    from mopidy import core


    class SoundspotFrontend(pykka.ThreadingActor, core.CoreListener):
        def __init__(self, config, core):
            super().__init__()
            self.config = config
            self.core = core

        # Your frontend implementation


Example backend
===============

If you want to extend Mopidy to support new music and playlist sources, you
want to implement a backend. A backend does not have access to Mopidy's core
API at all, but it does have a bunch of interfaces it can implement to extend
Mopidy.

The skeleton of a backend would look like this. See :ref:`backend-api` for more
details.

::

    import pykka

    from mopidy import backend


    class SoundspotBackend(pykka.ThreadingActor, backend.Backend):
        def __init__(self, config, audio):
            super().__init__()
            self.config = config
            self.audio = audio

        # Your backend implementation


Example command
===============

If you want to extend the Mopidy with a new helper not run from the server,
such as scanning for media, adding a command is the way to go. Your top level
command name will always match your extension name, but you are free to add
sub-commands with names of your choosing.

The skeleton of a command would look like this. See :ref:`commands-api` for
more details.

::

    from mopidy import commands


    class SoundspotCommand(commands.Command):
        help = "Some text that will show up in --help"

        def __init__(self):
            super().__init__()
            self.add_argument("--foo")

        def run(self, args, config, extensions):
           # Your command implementation
           return 0


Example web application
=======================

Extensions can use Mopidy's built-in web server to host static web clients as
well as WSGI web applications. For several examples, see the
:ref:`http-server-api` docs or explore with the `Mopidy-API-Explorer
<https://mopidy.com/ext/api-explorer>`_ extension.


Python conventions
==================

In general, it would be nice if Mopidy extensions followed the same
:ref:`codestyle` as Mopidy itself, as they're part of the same ecosystem.


Use of Mopidy APIs
==================

When writing an extension, you should only use APIs documented at
:ref:`api-ref`. Other parts of Mopidy, like :mod:`mopidy.internal`, may change
at any time and are not something extensions should use.

Mopidy performs type checking to help catch extension bugs. This applies to
both frontend calls into core and return values from backends. Additionally,
model fields always get validated to further guard against bad data.


Logging in extensions
=====================

For servers like Mopidy, logging is essential for understanding what's
going on. We use the :mod:`logging` module from Python's standard library. When
creating a logger, always namespace the logger using your Python package name
as this will be visible in Mopidy's debug log::

    import logging

    logger = logging.getLogger(__name__)

When logging at logging level ``info`` or higher (i.e. ``warning``, ``error``,
and ``critical``, but not ``debug``) the log message will be displayed to all
Mopidy users. Thus, the log messages at those levels should be well written and
easy to understand.

As the logger name is not included in Mopidy's default logging format, you
should make it obvious from the log message who is the source of the log
message. For example::

    Loaded 17 Soundspot playlists

Is much better than::

    Loaded 17 playlists

If you want to turn on debug logging for your own extension, but not for
everything else due to the amount of noise, see the docs for the
:confval:`loglevels/*` config section.


Making HTTP requests from extensions
====================================

Many Mopidy extensions need to make HTTP requests to use some web API. Here's a
few recommendations to those extensions.

Proxies
-------

If you make HTTP requests please make sure to respect the :ref:`proxy configs
<proxy-config>`, so that all the requests you make go through the proxy
configured by the Mopidy user. To make this easier for extension developers,
the helper function :func:`mopidy.httpclient.format_proxy` was added in Mopidy
1.1. This function returns the proxy settings `formatted the way Requests
expects <https://requests.readthedocs.io/en/latest/user/advanced/#proxies>`__.

User-Agent strings
------------------

When you make HTTP requests, it's helpful for debugging and usage analysis if
the client identifies itself with a proper User-Agent string. In Mopidy 1.1, we
added the helper function :func:`mopidy.httpclient.format_user_agent`.  Here's
an example of how to use it::

    >>> from mopidy import httpclient
    >>> import mopidy_soundspot
    >>> httpclient.format_user_agent(
    ...     f'{mopidy_soundspot.Extension.dist_name}/'
    ...     f'{mopidy_soundspot.__version__}'
    ... )
    'Mopidy-SoundSpot/2.0.0 Mopidy/4.0.0 Python/3.13.2'

Examples
--------

Most Mopidy extensions that make HTTP requests use either the `httpx
<https://www.python-httpx.org/>`_ or `Requests
<https://requests.readthedocs.io/>`_ library to do so.

Example using HTTPX
~~~~~~~~~~~~~~~~~~~

If you're using HTTPX, you can create a session object like this:

    import httpx
    from mopidy import httpclient

    import mopidy_soundspot

    client = httpx.Client(
        proxy=httpclient.format_proxy(proxy_config),
        headers={
            "user-agent": httpclient.format_user_agent(
                f"{mopidy_soundspot.Extension.dist_name}/{mopidy_soundspot.__version__}"
            ),
        }
    )
    response = client.get("https://example.com")

For further details, see HTTPX' docs on `clients
<https://www.python-httpx.org/advanced/clients/>`__.

Example using Requests
~~~~~~~~~~~~~~~~~~~~~~

When using Requests, the most convenient way to make sure the proxy and
User-Agent header is set properly is to create a Requests session object and use
that object to make all your HTTP requests::

    import requests
    from mopidy import httpclient

    import mopidy_soundspot


    def get_requests_session(proxy_config, user_agent):
        proxy = httpclient.format_proxy(proxy_config)
        full_user_agent = httpclient.format_user_agent(user_agent)

        session = requests.Session()
        session.proxies.update({"http": proxy, "https": proxy})
        session.headers.update({"user-agent": full_user_agent})

        return session


    # ``mopidy_config`` is the config object passed to your frontend/backend
    # constructor
    session = get_requests_session(
        proxy_config=mopidy_config["proxy"],
        user_agent=(
            f"{mopidy_soundspot.Extension.dist_name}/{mopidy_soundspot.__version__}"
        )
    )
    response = session.get("https://example.com")

For further details, see Requests' docs on `session objects
<https://requests.readthedocs.io/en/latest/user/advanced/#proxies>`__.


Testing extensions
==================

Creating test cases for your extensions makes them much simpler to maintain
over the long term. It can also make it easier for you to review and accept
pull requests from other contributors knowing that they will not break the
extension in some unanticipated way.

Before getting started, it is important to familiarize yourself with the
Python `mock library <https://docs.python.org/dev/library/unittest.mock.html>`_.

When it comes to running tests, Mopidy typically makes use of testing tools
like `tox <https://tox.readthedocs.io/>`_ and
`pytest <https://docs.pytest.org/>`_.

Testing approach
----------------

To a large extent the testing approach to follow depends on how your extension
is structured, which parts of Mopidy it interacts with, and if it uses any third
party APIs or makes any HTTP requests to the outside world.

The sections that follow contain code extracts that highlight some of the
key areas that should be tested. For more exhaustive examples, you may want to
take a look at the test cases that ship with Mopidy itself which covers
everything from instantiating various controllers, reading configuration files,
and simulating events that your extension can listen to.

In general your tests should cover the extension definition, the relevant
Mopidy controllers, and the backend and/or frontend Pykka actors that form part
of the extension.

Testing the extension definition
--------------------------------

Test cases for checking the definition of the extension should ensure that:

- the extension provides a ``ext.conf`` configuration file containing the
  relevant parameters with their default values,
- that the config schema is fully defined, and
- that the extension's actor(s) are added to the Mopidy registry on setup.

An example of what these tests could look like is provided below::

    def test_get_default_config():
        ext = Extension()
        config = ext.get_default_config()

        assert '[my_extension]' in config
        assert 'enabled = true' in config
        assert 'param_1 = value_1' in config
        assert 'param_2 = value_2' in config
        assert 'param_n = value_n' in config

    def test_get_config_schema():
        ext = Extension()
        schema = ext.get_config_schema()

        assert 'enabled' in schema
        assert 'param_1' in schema
        assert 'param_2' in schema
        assert 'param_n' in schema

    def test_setup():
        registry = mock.Mock()

        ext = Extension()
        ext.setup(registry)
        calls = [mock.call('frontend', frontend_lib.MyFrontend),
                 mock.call('backend',  backend_lib.MyBackend)]
        registry.add.assert_has_calls(calls, any_order=True)


Testing backend actors
----------------------

Backends can usually be constructed with a small mockup of the configuration
file, and mocking the audio actor::

    @pytest.fixture
    def config():
        return {
            'http': {
                'hostname': '127.0.0.1',
                'port': '6680'
            },
            'proxy': {
                'hostname': 'host_mock',
                'port': 'port_mock'
            },
            'my_extension': {
                'enabled': True,
                'param_1': 'value_1',
                'param_2': 'value_2',
                'param_n': 'value_n',
            }
        }

    def get_backend(config):
        return backend.MyBackend(config=config, audio=mock.Mock())

The following libraries might be useful for mocking any HTTP requests that
your extension makes:

- `pytest-httpx <https://pypi.org/project/pytest-httpx/>`_ - A pytest plugin for
  mocking HTTPX requests.
- `responses <https://pypi.org/project/responses>`_ - A utility library for
  mocking out the Requests Python library.
- `vcrpy <https://pypi.org/project/vcrpy>`_ - Automatically mock your HTTP
  interactions to simplify and speed up testing.

At the very least, you'll probably want to mock out the API's that you use to
avoid any unintended requests from being made by your backend during
testing.

Backend tests should also ensure that:

- the backend provides a unique URI scheme,
- that it sets up the various providers (e.g. library, playback, etc.)

::

    def test_uri_schemes(config):
        backend = get_backend(config)

        assert 'my_scheme' in backend.uri_schemes


    def test_init_sets_up_the_providers(config):
        backend = get_backend(config)

        assert isinstance(backend.library, library.MyLibraryProvider)
        assert isinstance(backend.playback, playback.MyPlaybackProvider)

Once you have a backend instance to work with, testing the various playback,
library, and other providers is straight forward and should not require any
special setup or processing.

Testing libraries
-----------------

Library test cases should cover the implementations of the standard Mopidy
API (e.g. ``browse``, ``lookup``, ``refresh``, ``get_images``, ``search``,
etc.)

Testing playback controllers
----------------------------

Testing ``change_track`` and ``translate_uri`` is probably the highest
priority, since these methods are used to prepare the track and provide its
audio URL to Mopidy's core for playback.

Testing frontends
-----------------

Because most frontends will interact with the Mopidy core, it will most likely
be necessary to have a full core running for testing purposes::

    self.core = core.Core.start(
        config,
        backends=[get_backend(config)],
    ).proxy()

It may be advisable to take a quick look at the
`Pykka API <https://pykka.readthedocs.io/>`_ at this point to make sure that
you are familiar with ``ThreadingActor``, ``ThreadingFuture``, and the
"proxies" that allow you to access the attributes and methods of the actor
directly.

You'll also need a list of :class:`~mopidy.models.Track` and a list of URIs in
order to populate the core with some simple tracks that can be used for
testing::

    tracks = [
        models.Track(uri='my_scheme:track:id1', length=40000),  # Regular track
        models.Track(uri='my_scheme:track:id2', length=None),   # No duration
    ]
    uris = [ 'my_scheme:track:id1', 'my_scheme:track:id2']

In the ``setup()`` method of your test class, you will then probably need to
monkey patch looking up tracks in the library (so that it will always use the
lists that you defined), and then populate the core's tracklist::

    def lookup(uris):
        result = {uri: [] for uri in uris}
        for track in self.tracks:
            if track.uri in result:
                result[track.uri].append(track)
        return result

    self.core.library.lookup = lookup
    self.tl_tracks = self.core.tracklist.add(uris=self.uris).get()


With all of that done you should finally be ready to instantiate your frontend::

    self.frontend = frontend.MyFrontend.start(config(), self.core).proxy()

Keep in mind that the normal core and frontend methods will usually return
``pykka.ThreadingFuture`` objects, so you will need to add ``.get()`` at
the end of most method calls in order to get to the actual return values.

Triggering events
-----------------

There may be test case scenarios that require simulating certain event triggers
that your extension's actors can listen for and respond on. An example for
patching the listener to store these events, and then play them back for your
actor, may look something like this::

    self.events = []
    self.patcher = mock.patch('mopidy.listener.send')
    self.send_mock = self.patcher.start()

    def send(cls, event, **kwargs):
        self.events.append((event, kwargs))

    self.send_mock.side_effect = send

Once all of the events have been captured, a method like
``replay_events()`` can be called at the relevant points in the code to have
the events fire::

    def replay_events(self, my_actor, until=None):
        while self.events:
            if self.events[0][0] == until:
                break
            event, kwargs = self.events.pop(0)
            frontend.on_event(event, **kwargs).get()

For further details and examples, refer to the
`/tests <https://github.com/mopidy/mopidy/tree/main/tests>`_
directory in the Mopidy repo.

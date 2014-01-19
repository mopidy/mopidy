.. _extensiondev:

*********************
Extension development
*********************

Mopidy started as simply an MPD server that could play music from Spotify.
Early on Mopidy got multiple "frontends" to expose Mopidy to more than just MPD
clients: for example the scrobbler frontend what scrobbles what you've listened
to to your Last.fm account, the MPRIS frontend that integrates Mopidy into the
Ubuntu Sound Menu, and the HTTP server and JavaScript player API making web
based Mopidy clients possible. In Mopidy 0.9 we added support for multiple
music sources without stopping and reconfiguring Mopidy: for example the local
backend for playing music from your disk, the stream backend for playing
Internet radio streams, and the Spotify and SoundCloud backends, for playing
music directly from those services.

All of these are examples of what you can accomplish by creating a Mopidy
extension. If you want to create your own Mopidy extension for something that
does not exist yet, this guide to extension development will help you get your
extension running in no time, and make it feel the way users would expect your
extension to behave.


Anatomy of an extension
=======================

Extensions are located in a Python package called ``mopidy_something`` where
"something" is the name of the application, library or web service you want to
integrated with Mopidy. So for example if you plan to add support for a service
named Soundspot to Mopidy, you would name your extension's Python package
``mopidy_soundspot``.

The extension must be shipped with a ``setup.py`` file and be registered on
`PyPI <https://pypi.python.org/>`_.  The name of the distribution on PyPI would
be something like "Mopidy-Soundspot". Make sure to include the name "Mopidy"
somewhere in that name and that you check the capitalization. This is the name
users will use when they install your extension from PyPI.

Also make sure the development version link in your package details work so
that people can easily install the development version into their virtualenv
simply by running e.g. ``pip install Mopidy-Soundspot==dev``.

Mopidy extensions must be licensed under an Apache 2.0 (like Mopidy itself),
BSD, MIT or more liberal license to be able to be enlisted in the Mopidy
documentation. The license text should be included in the ``LICENSE`` file in
the root of the extension's Git repo.

Combining this together, we get the following folder structure for our
extension, Mopidy-Soundspot::

    mopidy-soundspot/           # The Git repo root
        LICENSE                 # The license text
        MANIFEST.in             # List of data files to include in PyPI package
        README.rst              # Document what it is and how to use it
        mopidy_soundspot/       # Your code
            __init__.py
            ext.conf            # Default config for the extension
            ...
        setup.py                # Installation script

Example content for the most important files follows below.


cookiecutter project template
=============================

We've also made a `cookiecutter <http://cookiecutter.readthedocs.org/>`_
project template for `creating new Mopidy extensions
<https://github.com/mopidy/cookiecutter-mopidy-ext>`_. If you install
cookiecutter and run a single command, you're asked a few questions about the
name of your extension, etc. This is used to create a folder structure similar
to the above, with all the needed files and most of the details filled in for
you. This saves you a lot of tedious work and copy-pasting from this howto. See
the readme of `cookiecutter-mopidy-ext
<https://github.com/mopidy/cookiecutter-mopidy-ext>`_ for further details.


Example README.rst
==================

The README file should quickly tell what the extension does, how to install it,
and how to configure it. The README should contain a development snapshot link
to a tarball of the latest development version of the extension. It's important
that the development snapshot link ends with ``#egg=Mopidy-Something-dev`` for
installation using ``pip install Mopidy-Something==dev`` to work.

.. code-block:: rst

    ****************
    Mopidy-Soundspot
    ****************

    `Mopidy <http://www.mopidy.com/>`_ extension for playing music from
    `Soundspot <http://soundspot.example.com/>`_.

    Requires a Soundspot Platina subscription and the pysoundspot library.


    Installation
    ============

    Install by running::

        sudo pip install Mopidy-Soundspot

    Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
    <http://apt.mopidy.com/>`_.


    Configuration
    =============

    Before starting Mopidy, you must add your Soundspot username and password
    to the Mopidy configuration file::

        [soundspot]
        username = alice
        password = secret


    Project resources
    =================

    - `Source code <https://github.com/mopidy/mopidy-soundspot>`_
    - `Issue tracker <https://github.com/mopidy/mopidy-soundspot/issues>`_
    - `Download development snapshot <https://github.com/mopidy/mopidy-soundspot/tarball/master#egg=Mopidy-Soundspot-dev>`_


    Changelog
    =========

    v0.1.0 (2013-09-17)
    -------------------

    - Initial release.


Example setup.py
================

The ``setup.py`` file must use setuptools, and not distutils. This is because
Mopidy extensions use setuptools' entry point functionality to register
themselves as available Mopidy extensions when they are installed on your
system.

The example below also includes a couple of convenient tricks for reading the
package version from the source code so that it is defined in a single place,
and to reuse the README file as the long description of the package for the
PyPI registration.

The package must have ``install_requires`` on ``setuptools`` and ``Mopidy >=
0.14`` (or a newer version, if your extension requires it), in addition to any
other dependencies required by your extension. If you implement a Mopidy
frontend or backend, you'll need to include ``Pykka >= 1.1`` in the
requirements. The ``entry_points`` part must be included. The ``mopidy.ext``
part cannot be changed, but the innermost string should be changed. It's format
is ``ext_name = package_name:Extension``.  ``ext_name`` should be a short name
for your extension, typically the part after "Mopidy-" in lowercase. This name
is used e.g. to name the config section for your extension. The
``package_name:Extension`` part is simply the Python path to the extension
class that will connect the rest of the dots.

::

    from __future__ import unicode_literals

    import re
    from setuptools import setup, find_packages


    def get_version(filename):
        content = open(filename).read()
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
        return metadata['version']


    setup(
        name='Mopidy-Soundspot',
        version=get_version('mopidy_soundspot/__init__.py'),
        url='https://github.com/your-account/mopidy-soundspot',
        license='Apache License, Version 2.0',
        author='Your Name',
        author_email='your-email@example.com',
        description='Very short description',
        long_description=open('README.rst').read(),
        packages=find_packages(exclude=['tests', 'tests.*']),
        zip_safe=False,
        include_package_data=True,
        install_requires=[
            'setuptools',
            'Mopidy >= 0.14',
            'Pykka >= 1.1',
            'pysoundspot',
        ],
        test_suite='nose.collector',
        tests_require=[
            'nose',
            'mock >= 1.0',
        ],
        entry_points={
            'mopidy.ext': [
                'soundspot = mopidy_soundspot:Extension',
            ],
        },
        classifiers=[
            'Environment :: No Input/Output (Daemon)',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 2',
            'Topic :: Multimedia :: Sound/Audio :: Players',
        ],
    )

To make sure your README, license file and default config file is included in
the package that is uploaded to PyPI, we'll also need to add a ``MANIFEST.in``
file::

    include LICENSE
    include MANIFEST.in
    include README.rst
    include mopidy_soundspot/ext.conf

For details on the ``MANIFEST.in`` file format, check out the `distutils docs
<http://docs.python.org/2/distutils/sourcedist.html#manifest-template>`_.
`check-manifest <https://pypi.python.org/pypi/check-manifest>`_ is a very
useful tool to check your ``MANIFEST.in`` file for completeness.


Example __init__.py
===================

The ``__init__.py`` file should be placed inside the ``mopidy_soundspot``
Python package.

The root of your Python package should have an ``__version__`` attribute with a
:pep:`386` compliant version number, for example "0.1". Next, it should have a
class named ``Extension`` which inherits from Mopidy's extension base class,
:class:`mopidy.ext.Extension`. This is the class referred to in the
``entry_points`` part of ``setup.py``. Any imports of other files in your
extension should be kept inside methods. This ensures that this file can be
imported without raising :exc:`ImportError` exceptions for missing
dependencies, etc.

The default configuration for the extension is defined by the
``get_default_config()`` method in the ``Extension`` class which returns a
:mod:`ConfigParser` compatible config section. The config section's name must
be the same as the extension's short name, as defined in the ``entry_points``
part of ``setup.py``, for example ``soundspot``. All extensions must include
an ``enabled`` config which normally should default to ``true``. Provide good
defaults for all config values so that as few users as possible will need to
change them. The exception is if the config value has security implications; in
that case you should default to the most secure configuration. Leave any
configurations that doesn't have meaningful defaults blank, like ``username``
and ``password``. In the example below, we've chosen to maintain the default
config as a separate file named ``ext.conf``. This makes it easy to e.g.
include the default config in documentation without duplicating it.

This is ``mopidy_soundspot/__init__.py``::

    from __future__ import unicode_literals

    import logging
    import os

    import pygst
    pygst.require('0.10')
    import gst
    import gobject

    from mopidy import config, exceptions, ext


    __version__ = '0.1'

    # If you need to log, use loggers named after the current Python module
    logger = logging.getLogger(__name__)


    class Extension(ext.Extension):

        dist_name = 'Mopidy-Soundspot'
        ext_name = 'soundspot'
        version = __version__

        def get_default_config(self):
            conf_file = os.path.join(os.path.dirname(__file__, 'ext.conf'))
            return config.read(conf_file)

        def get_config_schema(self):
            schema = super(Extension, self).get_config_schema()
            schema['username'] = config.String()
            schema['password'] = config.Secret()
            return schema

        def get_command(self):
            from .commands import SoundspotCommand
            return SoundspotCommand()

        def validate_environment(self):
            # Any manual checks of the environment to fail early.
            # Dependencies described by setup.py are checked by Mopidy, so you
            # should not check their presence here.
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

            # Register a custom GStreamer element
            from .mixer import SoundspotMixer
            gobject.type_register(SoundspotMixer)
            gst.element_register(
                SoundspotMixer, 'soundspotmixer', gst.RANK_MARGINAL)

And this is ``mopidy_soundspot/ext.conf``:

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
            super(SoundspotFrontend, self).__init__()
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
            super(SoundspotBackend, self).__init__()
            self.audio = audio

        # Your backend implementation


Example command
===============

If you want to extend the Mopidy with a new helper not run from the server,
such as scanning for media, adding a command is the way to go. Your top level
command name will always match your extension name, but you are free to add
sub-commands with names of your choosing.

The skeleton of a commands would look like this. See :ref:`commands-api` for
more details.

::

    from mopidy import commands


    class SoundspotCommand(commands.Command):
        help = 'Some text that will show up in --help'

        def __init__(self):
            super(SoundspotCommand, self).__init__()
            self.add_argument('--foo')

        def run(self, args, config, extensions):
           # Your backend implementation
           return 0


Example GStreamer element
=========================

If you want to extend Mopidy's GStreamer pipeline with new custom GStreamer
elements, you'll need to register them in GStreamer before they can be used.

Basically, you just implement your GStreamer element in Python and then make
your :meth:`~mopidy.ext.Extension.setup` method register all your custom
GStreamer elements.

For examples of custom GStreamer elements implemented in Python, see
:mod:`mopidy.audio.mixers`.


Python conventions
==================

In general, it would be nice if Mopidy extensions followed the same
:ref:`codestyle` as Mopidy itself, as they're part of the same ecosystem. Among
other things, the code style guide explains why all the above examples start
with ``from __future__ import unicode_literals``.


Use of Mopidy APIs
==================

When writing an extension, you should only use APIs documented at
:ref:`api-ref`. Other parts of Mopidy, like :mod:`mopidy.utils`, may change at
any time, and is not something extensions should use.


Logging in extensions
=====================

When making servers like Mopidy, logging is essential for understanding what's
going on. We use the :mod:`logging` module from Python's standard library. When
creating a logger, always namespace the logger using your Python package name
as this will be visible in Mopidy's debug log::

    import logging

    logger = logging.getLogger('mopidy_soundspot')

    # Or even better, use the Python module name as the logger name:
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

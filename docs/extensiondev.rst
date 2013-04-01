*********************
Extension development
*********************

.. warning:: Draft

    This document is a draft open for discussion. It shows how we imagine that
    development of Mopidy extensions should become in the future, not how to
    currently develop an extension for Mopidy.


Mopidy started as simply an MPD server that could play music from Spotify.
Early on Mopidy got multiple "frontends" to expose Mopidy to more than just MPD
clients: for example the Last.fm frontend what scrobbles what you've listened
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

Extensions are all located in a Python package called ``mopidy_something``
where "something" is the name of the application, library or web service you
want to integrated with Mopidy. So for example if you plan to add support for a
service named Soundspot to Mopidy, you would name your extension's Python
package ``mopidy_soundspot``.

The name of the actual extension (the human readable name) however would be
something like "Mopidy-Soundspot". Make sure to include the name "Mopidy"
somewhere in that name and that you check the capitalization. This is the name
users will use when they install your extension from PyPI.

The extension must be shipped with a ``setup.py`` file and be registered on
`PyPI <https://pypi.python.org/>`_. Also make sure the development version link
in your package details work so that people can easily install the development
version into their virtualenv simply by running e.g. ``pip install
Mopidy-Soundspot==dev``.

Mopidy extensions must be licensed under an Apache 2.0 (like Mopidy itself),
BSD, MIT or more liberal license to be able to be enlisted in the Mopidy
documentation. The license text should be included in the ``LICENSE`` file in
the root of the extension's Git repo.

Combining this together, we get the following folder structure for our
extension, Mopidy-Soundspot::

    mopidy-soundspot/           # The Git repo root
        LICENSE                 # The license text
        README.rst              # Document what it is and how to use it
        mopidy_soundspot/       # Your code
            __init__.py
            ...
        setup.py                # Installation script

Example content for the most important files follows below.


Example README.rst
==================

The README file should quickly tell what the extension does, how to install it,
and how to configure it. The README should contain a development snapshot link
to a tarball of the latest development version of the extension. It's important
that the development snapshot link ends with ``#egg=mopidy-something-dev`` for
installation using ``pip install mopidy-something==dev`` to work.

.. code-block:: rst

    Mopidy-Soundspot
    ================

    `Mopidy <http://www.mopidy.com/>`_ extension for playing music from
    `Soundspot <http://soundspot.example.com/>`_.

    Usage
    -----

    Requires a Soundspot Platina subscription and the pysoundspot library.

    Install by running::

        sudo pip install Mopidy-Soundspot

    Or install the Debian/Ubuntu package from `apt.mopidy.com
    <http://apt.mopidy.com/>`_.

    Before starting Mopidy, you must add your Soundspot username and password
    to the Mopidy configuration file::

        [soundspot]
        username = alice
        password = secret

    Project resources
    -----------------

    - `Source code <https://github.com/mopidy/mopidy-soundspot>`_
    - `Issue tracker <https://github.com/mopidy/mopidy-soundspot/issues>`_
    - `Download development snapshot <https://github.com/mopidy/mopidy-soundspot/tarball/develop#egg=mopidy-soundspot-dev>`_


Example setup.py
================

The ``setup.py`` file must use setuptools/distribute, and not distutils. This
is because Mopidy extensions use setuptools' entry point functionality to
register themselves as available Mopidy extensions when they are installed on
your system.

The example below also includes a couple of convenient tricks for reading the
package version from the source code so that it it's just defined in a single
place, and to reuse the README file as the long description of the package for
the PyPI registration.

The package must have ``install_requires`` on ``setuptools`` and ``Mopidy``, in
addition to any other dependencies required by your extension. The
``entry_points`` part must be included. The ``mopidy.extension`` part cannot be
changed, but the innermost string should be changed. It's format is
``my_ext_name = my_py_module:MyExtClass``. ``my_ext_name`` should be a short
name for your extension, typically the part after "Mopidy-" in lowercase. This
name is used e.g. to name the config section for your extension. The
``my_py_module:MyExtClass`` part is simply the Python path to the extension
class that will connect the rest of the dots.

::

    from __future__ import unicode_literals

    import re
    from setuptools import setup


    def get_version(filename):
        content = open(filename).read()
        metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
        return metadata['version']


    setup(
        name='Mopidy-Soundspot',
        version=get_version('mopidy_soundspot/__init__.py'),
        url='http://example.com/mopidy-soundspot/',
        license='Apache License, Version 2.0',
        author='Your Name',
        author_email='your-email@example.com',
        description='Very short description',
        long_description=open('README.rst').read(),
        packages=['mopidy_soundspot'],
        # If you ship package instead of a single module instead, use
        # 'py_modules' instead of 'packages':
        #py_modules=['mopidy_soundspot'],
        zip_safe=False,
        include_package_data=True,
        install_requires=[
            'setuptools',
            'Mopidy',
            'pysoundspot',
        ],
        entry_points={
            b'mopidy.extension': [
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


Example __init__.py
===================

The ``__init__.py`` file should be placed inside the ``mopidy_soundspot``
Python package.

The root of your Python package should have an ``__version__`` attribute with a
:pep:`386` compliant version number, for example "0.1". Next, it should have a
class named ``Extension`` which inherits from Mopidy's extension base class.
This is the class referred to in the ``entry_points`` part of ``setup.py``. Any
imports of other files in your extension should be kept inside methods.  This
ensures that this file can be imported without raising :exc:`ImportError`
exceptions for missing dependencies, etc.

The default configuration for the extension is defined by the
``get_default_config()`` method in the ``Extension`` class which returns a
:mod:`ConfigParser` compatible config section. The config section's name should
be the same as the extension's short name, as defined in the ``entry_points``
part of ``setup.py``. All extensions should include an ``enabled`` config which
should default to ``true``. Provide good defaults for all config values so that
as few users as possible will need to change them. The exception is if the
config value has security implications; in that case you should default to the
most secure configuration. Leave any configurations that doesn't have
meaningful defaults blank, like ``username`` and ``password``.

::

    from __future__ import unicode_literals

    import os

    import pygst
    pygst.require('0.10')
    import gst
    import gobject

    from mopidy import ext
    from mopidy.exceptions import ExtensionError


    __version__ = '0.1'


    class Extension(ext.Extension):

        name = 'Mopidy-Soundspot'
        version = __version__

        def get_default_config(self):
            return """
                [soundspot]
                enabled = true
                username =
                password =
            """

        def validate_config(self, config):
            # ``config`` is the complete config document for the Mopidy
            # instance. The extension is free to check any config value it is
            # interested in, not just its own config values.

            if not config.getboolean('soundspot', 'enabled'):
                return
            if not config.get('soundspot', 'username'):
                raise ExtensionError('Config soundspot.username not set')
            if not config.get('soundspot', 'password'):
                raise ExtensionError('Config soundspot.password not set')

        def validate_environment(self):
            # This method can validate anything it wants about the environment
            # the extension is running in. Examples include checking if all
            # dependencies are installed.

            try:
                import pysoundspot
            except ImportError as e:
                raise ExtensionError('pysoundspot library not found', e)

        # You will typically only implement one of the next three methods
        # in a single extension.

        def get_frontend_classes(self):
            from .frontend import SoundspotFrontend
            return [SoundspotFrontend]

        def get_backend_classes(self):
            from .backend import SoundspotBackend
            return [SoundspotBackend]

        def register_gstreamer_elements(self):
            from .mixer import SoundspotMixer

            gobject.type_register(SoundspotMixer)
            gst.element_register(
                SoundspotMixer, 'soundspotmixer', gst.RANK_MARGINAL)


Example frontend
================

If you want to *use* Mopidy's core API from your extension, then you want to
implement a frontend.

The skeleton of a frontend would look like this. Notice that the frontend gets
passed a reference to the core API when it's created. See the
:ref:`frontend-api` for more details.

::

    import pykka

    from mopidy.core import CoreListener


    class SoundspotFrontend(pykka.ThreadingActor, CoreListener):
        def __init__(self, core):
            super(SoundspotFrontend, self).__init__()
            self.core = core

        # Your frontend implementation


Example backend
===============

If you want to extend Mopidy to support new music and playlist sources, you
want to implement a backend. A backend does not have access to Mopidy's core
API at all and got a bunch of interfaces to implement.

The skeleton of a backend would look like this. See :ref:`backend-api` for more
details.

::

    import pykka

    from mopidy.backends import base


    class SoundspotBackend(pykka.ThreadingActor, base.BaseBackend):
        def __init__(self, audio):
            super(SoundspotBackend, self).__init__()
            self.audio = audio

        # Your backend implementation


Example GStreamer element
=========================

If you want to extend Mopidy's GStreamer pipeline with new custom GStreamer
elements, you'll need to register them in GStreamer before they can be used.

Basically, you just implement your GStreamer element in Python and then make
your :meth:`Extension.register_gstreamer_elements` method register all your
custom GStreamer elements.

For examples of custom GStreamer elements implemented in Python, see
:mod:`mopidy.audio.mixers`.


Implementation steps
====================

A rough plan of how to make the above document the reality of how Mopidy
extensions work.

1. Implement :class:`mopidy.utils.ext.Extension` base class and the
   :exc:`mopidy.exceptions.ExtensionError` exception class.

2. Switch from using distutils to setuptools to package and install Mopidy so
   that we can register entry points for the bundled extensions and get
   information about all extensions available on the system from
   :mod:`pkg_resources`.

3. Add :class:`Extension` classes for all existing frontends and backends. Skip
   any default config and config validation for now.

4. Add entry points for the existing extensions in the ``setup.py`` file.

5. Rewrite the startup procedure to find extensions and thus frontends and
   backends via :mod:`pkg_resouces` instead of the ``FRONTENDS`` and
   ``BACKENDS`` settings.

6. Remove the ``FRONTENDS`` and ``BACKENDS`` settings.

7. Add default config files and config validation to all existing extensions.

8. Switch to ini file based configuration, using :mod:`ConfigParser`. The
   default config is the combination of a core config file plus the config from
   each installed extension. To find the effective config for the system, the
   following config sources are added together, with the later ones overriding
   the earlier ones:

   - the default config built from Mopidy core and all installed extensions,

   - ``/etc/mopidy/mopidy.conf``,

   - ``~/.config/mopidy/mopidy.conf``,

   - any config file provided via command line arguments, and

   - any config values provided via command line arguments.

9. Add command line options for:

   - loading an additional config file for this execution of Mopidy,

   - setting a config value for this execution of Mopidy,

   - printing the effective config and exit, and

   - write a config value permanently to ``~/.config/mopidy/mopidy.conf``, or
     ``/etc/mopidy/mopidy.conf`` if root, and exit.

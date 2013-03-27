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
Extension Registry. The license text should be included in the ``LICENSE`` file
in the root of the extension's Git repo.

Combining this together, we get the following folder structure for our
extension, Mopidy-Soundspot::

    mopidy-soundspot/           # The Git repo root
        mopidy_soundspot/       # The Python package
            __init__.py
        LICENSE                 # The license text
        README.rst              # Document what it is and how to use it
        setup.py                # Installation script

Example content for the most important files follows below.

README.rst
----------

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


setup.py
--------

::

    from setuptools import setup

    setup(
        name='Mopidy-Soundspot',
        version='1.0',
        url='http://example.com/mopidy-soundspot/',
        license='Apache License, Version 2.0',
        author='Your Name',
        author_email='your-email@example.com',
        description='Very short description',
        long_description=open('README.rst').read(),
        packages=['mopidy_soundspot'],
        zip_safe=False,
        include_package_data=True,
        platforms='any',
        install_requires=[
            'Mopidy',
            'pysoundspot',
        ],
        classifiers=[
            'Environment :: No Input/Output (Daemon)',
            'Intended Audience :: End Users/Desktop',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Multimedia :: Sound/Audio :: Players',
        ],
    )

Notes
=====

An extension wants to:

- Be automatically found if installed
  - Either register a setuptools entry points on installation, or
  - Require a line of configuration to activate the extension

- Provide default config

- Validate configuration

  - Pass all configuration to every extension, let the extension complain on
    anything it wants to

- Validate presence of dependencies

  - Python packages (e.g. pyspotify)

  - Other software

  - The presence of other extensions can be validated in the configuration
    validation step

- Validate that needed TCP ports are free

- Register new GStreamer elements

- Be asked to start running

- Be asked to shut down

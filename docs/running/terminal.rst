.. _terminal:

*********************
Running in a terminal
*********************

For most users, it is probably preferable to run Mopidy as a :ref:`service
<service>` so that Mopidy is automatically started when your system starts.

The primary use case for running Mopidy manually in a terminal is that you're
developing on Mopidy or a Mopidy extension yourself, and are interested in
seeing the log output all the time and to be able to quickly start and
restart Mopidy.


Starting
========

To start Mopidy manually, simply open a terminal and run::

    mopidy

For a complete reference to the Mopidy commands and their command line options,
see :ref:`mopidy-cmd`.

You can also get some help directly in the terminal by running::

    mopidy --help


Stopping
========

To stop Mopidy, press ``CTRL+C`` in the terminal where you started Mopidy.

Mopidy will also shut down properly if you send it the ``TERM`` signal to the
Mopidy process, e.g. by using ``pkill`` in another terminal::

    pkill mopidy


Configuration
=============

When running Mopidy for the first time, it'll create a configuration
file for you, usually at :file:`~/.config/mopidy/mopidy.conf`.

The ``~`` in the file path automatically expands to your *home directory*.
If your username is ``alice`` and you are running Linux, the config file will
probably be at :file:`/home/alice/.config/mopidy/mopidy.conf`.

As this might vary slightly from system to system, you can check
the first few lines of output from Mopidy to confirm the exact location:

.. code:: text

    INFO     2019-12-21 23:17:31,236 [20617:MainThread] mopidy.config
      Loading config from builtin defaults
    INFO     2019-12-21 23:17:31,237 [20617:MainThread] mopidy.config
      Loading config from command line options
    INFO     2019-12-21 23:17:31,239 [20617:MainThread] mopidy.internal.path
      Creating dir file:///home/jodal/.config/mopidy
    INFO     2019-12-21 23:17:31,240 [20617:MainThread] mopidy.config
      Loading config from builtin defaults
    INFO     2019-12-21 23:17:31,241 [20617:MainThread] mopidy.config
      Loading config from command line options
    INFO     2019-12-21 23:17:31,249 [20617:MainThread] mopidy.internal.path
      Creating file file:///home/jodal/.config/mopidy/mopidy.conf
    INFO     2019-12-21 23:17:31,249 [20617:MainThread] mopidy.__main__
      Initialized /home/jodal/.config/mopidy/mopidy.conf with default config

To print Mopidy's *effective* configuration, i.e. the combination of defaults,
your configuration file, and any command line options, you can run::

    mopidy config

This will print your full effective config with passwords masked out so that
you safely can share the output with others for debugging.

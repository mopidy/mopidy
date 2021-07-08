.. _troubleshooting:

***************
Troubleshooting
***************

When you're debugging yourself or asking for help, there are some tools built
into Mopidy that you should know about.


Getting help
============

If you get stuck, you can get help at the our `Discourse forum
<https://discourse.mopidy.com/>`_ or in the ``#mopidy-users`` stream on `Zulip
chat <https://mopidy.zulipchat.com/>`_.

If you stumble into a bug or have a feature request, please create an issue in
the `issue tracker <https://github.com/mopidy/mopidy/issues>`_. If you're
unsure if it's a bug or not, ask for help in the forum or the chat first. The
`source code <https://github.com/mopidy/mopidy>`_ may also be of help.


.. _show-config:

Show effective configuration
============================

The ``config`` subcommand will print your full effective
configuration the way Mopidy sees it after all defaults and all config files
have been merged into a single config document. Any secret values like
passwords are masked out, so the output of the command should be safe to share
with others for debugging.

If you run Mopidy manually in a terminal, run::

    mopidy config

If you run Mopidy as a system service, run::

    sudo mopidyctl config


.. _show-deps:

Show installed dependencies
===========================

The ``deps`` subcommand will list the paths to and versions of
any dependency Mopidy or the extensions might need to work. This is very useful
data for checking that you're using the right versions, and that you're using
the right installation if you have multiple installations of a dependency on
your system.

If you run Mopidy manually in a terminal, run::

    mopidy deps

If you run Mopidy as a system service, run::

    sudo mopidyctl deps


Debug logging
=============

If you run :option:`mopidy -v` or ``mopidy -vv``, ``mopidy -vvv``,
or ``mopidy -vvvv`` Mopidy will print more and more debug log to ``stderr``.
All four options will give you debug level output from Mopidy and extensions,
while ``-vv``, ``-vvv``, and ``-vvvv`` will give you more log output
from their dependencies as well.

To save a debug log to file for sharing with others, you can pipe ``stdout``
and ``stderr`` to a file::

    mopidy -vvvv 2>&1 | tee mopidy.log

If you run Mopidy as a system service, adding arguments on the command line
might be complicated. As an alternative, you can set the configuration
:confval:`logging/verbosity` to ``4`` instead of passing ``-vvvv`` on the
command line:

.. code-block:: ini

    [logging]
    verbosity = 4

If you run Mopidy as a system service and are using journald,
like most modern Linux systems, you can view the Mopidy log by running::

    sudo journalctl -u mopidy

To save the output to a file for sharing, run::

    sudo journalctl -u mopidy | tee mopidy.log

If you want to reduce the logging for some component, see the
docs for the :confval:`loglevels/*` config section.

For example, to only get error log messages from requests, even when running
with maximum verbosity, you can add the following to :file:`mopidy.conf`:

.. code-block:: ini

    [loglevels]
    requests = error


Track metadata
==============

If you find missing or incorrect metadata for a track, or are experiencing
problems during local scanning, you can manually view track metadata as seen by
Mopidy by running::

    python3 -m mopidy.audio.scan path_to_your_file

It may be useful to compare that output against other music playback software
or audio tagging tools. One such tool is GStreamer's own ``gst-discoverer-1.0``
which can be installed with ``sudo apt install gstreamer1.0-plugins-base-apps``
and invoked by running::

    gst-discoverer-1.0 path_to_your_file

Mopidy relies on GStreamer library functions to handle audio metadata so if you
find ``gst-discoverer-1.0`` is also unable to correctly read the metadata, but
other software succeeds, then the problem is likely to be with GStreamer itself.
In this situation you will likely find the behaviour is dependent on the version
of GStreamer being used and/or the file format.


Debugging deadlocks
===================

If Mopidy hangs without an obvious explanation, you can send the ``SIGUSR1``
signal to the Mopidy process. If Mopidy's main thread is still responsive, it
will log a traceback for each running thread, showing what the threads are
currently doing. This is a very useful tool for understanding exactly how the
system is deadlocking. If you have the ``pkill`` command installed, you can use
this by simply running::

    pkill -SIGUSR1 mopidy

You can read more about the deadlock debug helper in the
`Pykka documentation <https://pykka.readthedocs.io/en/latest/api/debug/>`_.


Debugging GStreamer
===================

If you really want to dig in and debug GStreamer behaviour, then check out the
`Debugging section
<https://gstreamer.freedesktop.org/documentation/application-development/appendix/checklist-element.html?gi-language=python>`_
of GStreamer's documentation for your options. Note that Mopidy does not
support the GStreamer command line options, like ``--gst-debug-level=3``, but
setting GStreamer environment variables, like :envvar:`GST_DEBUG`, works with
Mopidy. For example, to run Mopidy with debug logging and GStreamer logging at
level 3, you can run::

    GST_DEBUG=3 mopidy -v

This will produce a lot of output, but given some GStreamer knowledge this is
very useful for debugging GStreamer pipeline issues. Additionally
:envvar:`GST_DEBUG_FILE=gstreamer.log` can be used to redirect the debug
logging to a file instead of ``stdout``.

Lastly :envvar:`GST_DEBUG_DUMP_DOT_DIR` can be used to get descriptions of the
current pipeline in dot format. Currently we trigger a dump of the pipeline on
every completed state change::

    GST_DEBUG_DUMP_DOT_DIR=. mopidy

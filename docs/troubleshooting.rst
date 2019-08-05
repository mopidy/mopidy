.. _troubleshooting:

***************
Troubleshooting
***************

If you run into problems with Mopidy, we usually hang around at ``#mopidy`` on
`irc.freenode.net <http://freenode.net/>`_ and also have a `discussion forum
<https://discourse.mopidy.com/c/mopidy>`_.
If you stumble into a bug or have a feature request, please create an issue in
the `issue tracker <https://github.com/mopidy/mopidy/issues>`_.

When you're debugging yourself or asking for help, there are some tools built
into Mopidy that you should know about.


Sharing config and log output
=============================

If you're getting help at IRC, we recommend that you use a pastebin, like
`pastebin.com <https://pastebin.com/>`_ or `GitHub Gist
<https://gist.github.com/>`_, to share your configuration and log output.
Pasting more than a couple of lines on IRC is generally frowned upon. On the
mailing list or when reporting an issue, somewhat longer text dumps are
accepted, but large logs should still be shared through a pastebin.


Show effective configuration
============================

The command ``mopidy config`` will print your full effective
configuration the way Mopidy sees it after all defaults and all config files
have been merged into a single config document. Any secret values like
passwords are masked out, so the output of the command should be safe to share
with others for debugging.


Show installed dependencies
===========================

The command ``mopidy deps`` will list the paths to and versions of
any dependency Mopidy or the extensions might need to work. This is very useful
data for checking that you're using the right versions, and that you're using
the right installation if you have multiple installations of a dependency on
your system.


Debug logging
=============

If you run :option:`mopidy -v` or ``mopidy -vv``, ``mopidy -vvv``,
or ``mopidy -vvvv`` Mopidy will print more and more debug log to stdout.
All four options will give you debug level output from Mopidy and extensions,
while ``-vv``, ``-vvv``, and ``-vvvv`` will give you more log output
from their dependencies as well.

To save a debug log to file for sharing with others, you can run
``mopidy -vvvv | tee mopidy.log``.

If you run Mopidy as a system service, adding arguments on the command line
might be complicated. As an alternative, you can set the configuration
:confval:`logging/verbosity` to ``4`` instead of passing ``-vvvv`` on the
command line.

If you run Mopidy as a system service and are using journald,
like most modern Linux systems, you can view the Mopidy log by running
``sudo journalctl -u mopidy``. To save the output to a file for sharing, run
``sudo journalctl -u mopidy | tee mopidy.log``.

If you want to reduce the logging for some component, see the
docs for the :confval:`loglevels/*` config section.


Debugging deadlocks
===================

If Mopidy hangs without an obvious explanation, you can send the ``SIGUSR1``
signal to the Mopidy process. If Mopidy's main thread is still responsive, it
will log a traceback for each running thread, showing what the threads are
currently doing. This is a very useful tool for understanding exactly how the
system is deadlocking. If you have the ``pkill`` command installed, you can use
this by simply running::

    pkill -SIGUSR1 mopidy


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
logging to a file instead of standard out.

Lastly :envvar:`GST_DEBUG_DUMP_DOT_DIR` can be used to get descriptions of the
current pipeline in dot format. Currently we trigger a dump of the pipeline on
every completed state change::

    GST_DEBUG_DUMP_DOT_DIR=. mopidy

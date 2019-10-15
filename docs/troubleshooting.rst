.. _troubleshooting:

***************
Troubleshooting
***************

If you get stuck, you can get help at the our `Discourse forum
<https://discourse.mopidy.com/>`_ or in the ``#mopidy-users`` stream on `Zulip
chat <https://mopidy.zulipchat.com/>`_.

If you stumble into a bug or have a feature request, please create an issue in
the `issue tracker <https://github.com/mopidy/mopidy/issues>`_. If you're
unsure if it's a bug or not, ask for help in the forum or the chat first. The
`source code <https://github.com/mopidy/mopidy>`_ may also be of help.

When you're debugging yourself or asking for help, there are some tools built
into Mopidy that you should know about.


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

If you run :option:`mopidy -v` or ``mopidy -vv`` or ``mopidy -vvv`` Mopidy will
print more and more debug log to stdout. All three options will give you debug
level output from Mopidy and extensions, while ``-vv`` and ``-vvv`` will give
you more log output from their dependencies as well.

If you run :option:`mopidy --save-debug-log`, it will save the log equivalent
with ``-vvv`` to the file ``mopidy.log`` in the directory you ran the command
from.

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

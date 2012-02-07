**********************
GStreamer installation
**********************

To use the Mopidy, you first need to install GStreamer and the GStreamer Python
bindings.


Installing GStreamer on Linux
=============================

GStreamer is packaged for most popular Linux distributions. Search for
GStreamer in your package manager, and make sure to install the Python
bindings, and the "good" and "ugly" plugin sets.


Debian/Ubuntu
-------------

If you use Debian/Ubuntu you can install GStreamer like this::

    sudo apt-get install python-gst0.10 gstreamer0.10-plugins-good \
        gstreamer0.10-plugins-ugly

If you install Mopidy from our APT archive, you don't need to install GStreamer
yourself. The Mopidy Debian package will handle it for you.


Arch Linux
----------

If you use Arch Linux, install the following packages from the official
repository::

    sudo pacman -S gstreamer0.10-python gstreamer0.10-good-plugins \
        gstreamer0.10-ugly-plugins


Installing GStreamer on OS X
============================

.. note::

    We have been working with `Homebrew <https://github.com/mxcl/homebrew>`_ to
    make all the GStreamer packages easily installable on OS X using Homebrew.
    We've gotten most of our packages included, but the Homebrew guys aren't
    very happy to include Python specific packages into Homebrew, even though
    they are not installable by pip. If you're interested, see the discussion
    in `Homebrew's issue #1612
    <https://github.com/mxcl/homebrew/issues/issue/1612>`_ for details.

The following is currently the shortest path to installing GStreamer with
Python bindings on OS X using Homebrew.

#. Install `Homebrew <https://github.com/mxcl/homebrew>`_.

#. Download our Homebrew formulas for ``pycairo``, ``pygobject``, ``pygtk``,
   and ``gst-python``::

      curl -o $(brew --prefix)/Library/Formula/pycairo.rb \
          https://raw.github.com/jodal/homebrew/gst-python/Library/Formula/pycairo.rb
      curl -o $(brew --prefix)/Library/Formula/pygobject.rb \
          https://raw.github.com/jodal/homebrew/gst-python/Library/Formula/pygobject.rb
      curl -o $(brew --prefix)/Library/Formula/pygtk.rb \
          https://raw.github.com/jodal/homebrew/gst-python/Library/Formula/pygtk.rb
      curl -o $(brew --prefix)/Library/Formula/gst-python.rb \
          https://raw.github.com/jodal/homebrew/gst-python/Library/Formula/gst-python.rb

#. Install the required packages::

      brew install gst-python gst-plugins-good gst-plugins-ugly

#. Make sure to include Homebrew's Python ``site-packages`` directory in your
   ``PYTHONPATH``. If you don't include this, Mopidy will not find GStreamer
   and crash.

   You can either amend your ``PYTHONPATH`` permanently, by adding the
   following statement to your shell's init file, e.g. ``~/.bashrc``::

       export PYTHONPATH=$(brew --prefix)/lib/python2.6/site-packages:$PYTHONPATH

   Or, you can prefix the Mopidy command every time you run it::

       PYTHONPATH=$(brew --prefix)/lib/python2.6/site-packages mopidy

   Note that you need to replace ``python2.6`` with ``python2.7`` if that's
   the Python version you are using. To find your Python version, run::

       python --version


Testing the installation
========================

If you now run the ``gst-inspect-0.10`` command (the version number may vary),
you should see a long listing of installed plugins, ending in a summary line::

    $ gst-inspect-0.10
    ... long list of installed plugins ...
    Total count: 218 plugins (1 blacklist entry not shown), 1031 features

You should be able to produce a audible tone by running::

    gst-launch-0.10 audiotestsrc ! autoaudiosink

If you cannot hear any sound when running this command, you won't hear any
sound from Mopidy either, as Mopidy uses GStreamer's ``autoaudiosink`` to play
audio. Thus, make this work before you continue installing Mopidy.


Using a custom audio sink
=========================

If you for some reason want to use some other GStreamer audio sink than
``autoaudiosink``, you can add ``mopidy.outputs.custom.CustomOutput`` to the
:attr:`mopidy.settings.OUTPUTS` setting, and set the
:attr:`mopidy.settings.CUSTOM_OUTPUT` setting to a partial GStreamer pipeline
description describing the GStreamer sink you want to use.

Example of ``settings.py`` for OSS4::

    OUTPUTS = (u'mopidy.outputs.custom.CustomOutput',)
    CUSTOM_OUTPUT = u'oss4sink'

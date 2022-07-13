*****
macOS
*****

If you are running macOS, you can install everything needed with Homebrew.


Install from Homebrew
=====================

#. Make sure you have `Homebrew <https://brew.sh/>`_ installed.

#. Make sure your Homebrew installation is up to date before you continue::

       brew upgrade

   Note that this will upgrade all software on your system that have been
   installed with Homebrew.

#. Mopidy has its own `Homebrew formula repo
   <https://github.com/mopidy/homebrew-mopidy>`_, called a "tap".
   To enable our Homebrew tap, run::

       brew tap mopidy/mopidy

#. To install Mopidy, run::

       brew install mopidy

   This will take some time, as it will also install Mopidy's dependency
   GStreamer, which again depends on a huge number of media codecs.

#. Now, you're ready to :ref:`run Mopidy <running>`.


Upgrading
=========

When a new release of Mopidy is out, and you can't wait for you system to
figure it out for itself, run the following to upgrade right away::

    brew upgrade


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, the Homebrew tap has formulas for several Mopidy extensions as
well. Extensions installed from Homebrew will come complete with all
dependencies, both Python and non-Python ones.

To list all the extensions available from our tap, you can run::

    brew search mopidy

If you cannot find the extension you want in the Homebrew search result,
you caninstall it from PyPI using ``pip`` instead.
Even if Mopidy itself is installed from Homebrew it will correctly detect and
use extensions from PyPI installed globally on your system using::

   python3 -m pip install ...

.. note::
    Homebrew documents ``pip3 install ...`` as the way to install packages from
    PyPI. This has the exact same effect as ``python3 -m pip install ...``.
    We keep to the latter variant to keep our PyPI installation instructions
    identical across operating systems and distributions.

For a comprehensive index of available Mopidy extensions,
including those not installable from APT,
see the `Mopidy extension registry <https://mopidy.com/ext/>`_.

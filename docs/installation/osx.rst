***************************
OS X: Install from Homebrew
***************************

If you are running OS X, you can install everything needed with Homebrew.

#. Install Xcode command line developer tools. Do this even if you already have
   Xcode installed::

       xcode-select --install

#. Install `XQuartz <http://xquartz.macosforge.org/>`_. This is needed by
   GStreamer which Mopidy use heavily.

#. Install `Homebrew <https://github.com/Homebrew/homebrew>`_.

#. If you are already using Homebrew, make sure your installation is up to
   date before you continue::

       brew upgrade

   Note that this will upgrade all software on your system that have been
   installed with Homebrew.

#. Mopidy works out of box if you have installed Python from Homebrew::

       brew install python

   .. note::

       If you want to use the Python version bundled with OS X, you'll need to
       include Python packages installed by Homebrew in your ``PYTHONPATH``.
       If you don't do this, the ``mopidy`` executable will not find its
       dependencies and will crash.

       You can either amend your ``PYTHONPATH`` permanently, by adding the
       following statement to your shell's init file, e.g. ``~/.bashrc``::

           export PYTHONPATH=$(brew --prefix)/lib/python2.7/site-packages:$PYTHONPATH

       And then reload the shell's init file or restart your terminal::

           source ~/.bashrc

       Or, you can prefix the Mopidy command every time you run it::

           PYTHONPATH=$(brew --prefix)/lib/python2.7/site-packages mopidy

#. Mopidy has its own `Homebrew formula repo
   <https://github.com/mopidy/homebrew-mopidy>`_, called a "tap". To enable our
   Homebrew tap, run::

       brew tap mopidy/mopidy

#. To install Mopidy, run::

       brew install mopidy

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.


Installing extensions
=====================

If you want to use any Mopidy extensions, like Spotify support or Last.fm
scrobbling, the Homebrew tap has formulas for several Mopidy extensions as
well. Extensions installed from Homebrew will come complete with all
dependencies, both Python and non-Python ones.

To list all the extensions available from our tap, you can run::

    brew search mopidy

You can also install any Mopidy extension directly from PyPI with ``pip``, just
like on Linux. To list all the extensions available from PyPI, run::

    pip search mopidy

Note that extensions installed from PyPI will only automatically install Python
dependencies. Please refer to the extension's documentation for information
about any other requirements needed for the extension to work properly.

For a full list of available Mopidy extensions, including those not installable
from Homebrew, see :ref:`ext`.


.. _osx-service:

Running Mopidy automatically on login
=====================================

On OS X, you can use launchd to start Mopidy automatically at login.

If you installed Mopidy from Homebrew, simply run ``brew info mopidy`` and
follow the instructions in the "Caveats" section::

    $ brew info mopidy
    ...
    ==> Caveats
    To have launchd start mopidy at login:
        ln -sfv /usr/local/opt/mopidy/*.plist ~/Library/LaunchAgents
    Then to load mopidy now:
        launchctl load ~/Library/LaunchAgents/homebrew.mopidy.mopidy.plist
    Or, if you don't want/need launchctl, you can just run:
        mopidy

If you happen to be on OS X, but didn't install Mopidy with Homebrew, you can
get the same effect by adding the file
:file:`~/Library/LaunchAgents/mopidy.plist` with the following contents::

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
      <key>Label</key>
      <string>mopidy</string>
      <key>ProgramArguments</key>
      <array>
        <string>/usr/local/bin/mopidy</string>
      </array>
      <key>RunAtLoad</key>
      <true/>
      <key>KeepAlive</key>
      <true/>
    </dict>
    </plist>

You might need to adjust the path to the ``mopidy`` executable,
``/usr/local/bin/mopidy``, to match your system.

Then, to start Mopidy with launchd right away::

    launchctl load ~/Library/LaunchAgents/mopidy.plist

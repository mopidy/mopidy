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

       brew update
       brew upgrade

   Notice that this will upgrade all software on your system that have been
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

#. Optional: If you want to use any Mopidy extensions, like Spotify support or
   Last.fm scrobbling, the Homebrew tap has formulas for several Mopidy
   extensions as well.

   To list all the extensions available from our tap, you can run::

       brew search mopidy

   For a full list of available Mopidy extensions, including those not
   installable from Homebrew, see :ref:`ext`.

#. Finally, you need to set a couple of :doc:`config values </config>`, and
   then you're ready to :doc:`run Mopidy </running>`.

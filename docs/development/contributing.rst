*****************
How to contribute
*****************

Development of Mopidy is coordinated through the IRC channel ``#mopidy`` at
``irc.freenode.net`` and through `GitHub <http://github.com/>`_.


Code style
==========

We generally follow the :pep:`8` style guidelines, with a couple of notable
exceptions:

- We indent continuation lines with four spaces more than the previous line.
  For example::

    from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
        BasePlaybackController, BaseLibraryController,
        BaseStoredPlaylistsController)

  And *not*::

    from mopidy.backends import (BaseBackend, BaseCurrentPlaylistController,
                                 BasePlaybackController, BaseLibraryController,
                                 BaseStoredPlaylistsController)

- An exception to the previous exception: When continuing control flow
  statements like ``if``, ``for`` and ``while``, we indent with eight spaces
  more than the previous line. In other words, the line is indented one level
  further to the right than the following block of code. For example::

    if (old_state in (self.PLAYING, self.STOPPED)
            and new_state == self.PLAYING):
        self._play_time_start()

  And *not*::

    if (old_state in (self.PLAYING, self.STOPPED)
        and new_state == self.PLAYING):
        self._play_time_start()


Running tests
=============

To run tests, you need a couple of dependencies. They can be installed through
Debian/Ubuntu package management::

    sudo aptitude install python-coverage python-nose

Or, they can be installed using ``pip``::

    sudo pip install -r requirements-tests.txt

Then, to run all tests, go to the project directory and run::

    nosetests

For example::

    $ nosetests
    ......................................................................
    ......................................................................
    ......................................................................
    .......
    ----------------------------------------------------------------------
    Ran 217 tests in 0.267s

    OK

To run tests with test coverage statistics::

    nosetests --with-coverage

For more documentation on testing, check out the `nose documentation
<http://somethingaboutorange.com/mrl/projects/nose/>`_.

.. note::

    The test coverage report at http://www.mopidy.com/coverage/ is
    automatically updated within 10 minutes after an update is pushed to
    ``jodal/mopidy/master`` at GitHub.


Writing documentation
=====================

To write documentation, we use `Sphinx <http://sphinx.pocoo.org/>`_. See their
site for lots of documentation on how to use Sphinx. To generate HTML or LaTeX
from the documentation files, you need some additional dependencies.

You can install them through Debian/Ubuntu package management::

    sudo aptitude install python-sphinx python-pygraphviz graphviz

Then, to generate docs::

    cd docs/
    make        # For help on available targets
    make html   # To generate HTML docs

.. note::

    The documentation at http://www.mopidy.com/docs/ is automatically updated
    within 10 minutes after a documentation update is pushed to
    ``jodal/mopidy/master`` at GitHub.


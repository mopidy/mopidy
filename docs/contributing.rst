.. _contributing:

************
Contributing
************

If you are thinking about making Mopidy better, or you just want to hack on it,
that’s great. Here are some tips to get you started.


Getting started
===============

#. Make sure you have a `GitHub account <https://github.com/signup/free>`_.

#. `Submit <https://github.com/mopidy/mopidy/issues/new>`_ a ticket for your
   issue, assuming one does not already exist. Clearly describe the issue
   including steps to reproduce when it is a bug.

#. Fork the repository on GitHub.


Making changes
==============

#. Clone your fork on GitHub to your computer.

#. Consider making a Python `virtualenv <http://www.virtualenv.org/>`_ for
   Mopidy development to wall of Mopidy and it's dependencies from the rest of
   your system. If you do so, create the virtualenv with the
   ``--system-site-packages`` flag so that Mopidy can use globally installed
   dependencies like GStreamer. If you don't use a virtualenv, you may need to
   run the following ``pip`` and ``python setup.py`` commands with ``sudo`` to
   install stuff globally on your computer.

#. Install dependencies as described in the :ref:`installation` section.

#. Checkout a new branch (usually based on ``develop``) and name it accordingly
   to what you intend to do.

   - Features get the prefix ``feature/``

   - Bug fixes get the prefix ``fix/``

   - Improvements to the documentation get the prefix ``docs/``


.. _run-from-git:

Running Mopidy from Git
=======================

If you want to hack on Mopidy, you should run Mopidy directly from the Git
repo.

#. Go to the Git repo root::

       cd mopidy/

#. To get a ``mopidy`` executable and register all bundled extensions with
   setuptools, run::

      python setup.py develop

   It still works to run ``python mopidy`` directly on the ``mopidy`` Python
   package directory, but if you have never run ``python setup.py develop`` the
   extensions bundled with Mopidy isn't registered with setuptools, so Mopidy
   will start without any frontends or backends, making it quite useless.

#. Now you can run the Mopidy command, and it will run using the code
   in the Git repo::

      mopidy

   If you do any changes to the code, you'll just need to restart ``mopidy``
   to see the changes take effect.


Testing
=======

Mopidy has quite good test coverage, and we would like all new code going into
Mopidy to come with tests.

#. To run tests, you need a couple of dependencies. They can be installed using
   ``pip``::

       pip install --upgrade coverage flake8 mock nose

#. Then, to run all tests, go to the project directory and run::

       nosetests

   To run tests with test coverage statistics, remember to specify the tests
   dir::

       nosetests --with-coverage tests/

#. Check the code for errors and style issues using flake8::

       flake8 .

For more documentation on testing, check out the `nose documentation
<http://nose.readthedocs.org/>`_.


Submitting changes
==================

- One branch per feature or fix. Keep branches small and on topic.

- Follow the :ref:`code style <codestyle>`, especially make sure ``flake8``
  does not complain about anything.

- Write good commit messages. Here's three blog posts on how to do it right:

  - `Writing Git commit messages
    <http://365git.tumblr.com/post/3308646748/writing-git-commit-messages>`_

  - `A Note About Git Commit Messages
    <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_

  - `On commit messages
    <http://who-t.blogspot.ch/2009/12/on-commit-messages.html>`_

- Send a pull request to the ``develop`` branch. See the `GitHub pull request
  docs <https://help.github.com/articles/using-pull-requests>`_ for help.


Additional resources
====================

- IRC channel: ``#mopidy`` at `irc.freenode.net <http://freenode.net/>`_

- `Issue tracker <https://github.com/mopidy/mopidy/issues>`_

- `Mailing List <https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_

- `GitHub documentation <https://help.github.com/>`_

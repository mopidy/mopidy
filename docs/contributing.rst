.. _contributing:

************
Contributing
************

If you are thinking about making Mopidy better, or you just want to hack on it,
that’s great. Here are some tips to get you started.


Getting started
===============

1. Make sure you have a `GitHub account <https://github.com/signup/free>`_.

2. `Submit <https://github.com/mopidy/mopidy/issues/new>`_ a ticket for your
   issue, assuming one does not already exist. Clearly describe the issue
   including steps to reproduce when it is a bug.

3. Fork the repository on GitHub.


Making changes
==============

1. Clone your fork on GitHub to your computer.

2. Install dependencies as described in the :ref:`installation` section.

3. Checkout a new branch (usually based on develop) and name it accordingly to
   what you intend to do.

   - Features get the prefix ``feature/``

   - Bug fixes get the prefix ``fix/``

   - Improvements to the documentation get the prefix ``docs/``


Testing
=======

Mopidy got quite good test coverage, and we would like all new code going into
Mopidy to come with tests.

1. To run tests, you need a couple of dependencies. They can be installed using
   ``pip``::

       pip install -r requirements/tests.txt

2. Then, to run all tests, go to the project directory and run::

       nosetests

   To run tests with test coverage statistics, remember to specify the tests
   dir::

       nosetests --with-coverage tests/

3. Check the code for errors and style issues using flake8::

       flake8 .

For more documentation on testing, check out the `nose documentation
<http://nose.readthedocs.org/>`_.


Submitting changes
==================

- One branch per feature or fix.

- Follow the style guide, especially make sure ``flake8`` does not complain
  about anything.

- Send a pull request to the ``develop`` branch.


Additional resources
====================

- `Issue tracker <https://github.com/mopidy/mopidy/issues>`_

- `Mailing List <https://groups.google.com/forum/?fromgroups=#!forum/mopidy>`_

- `General GitHub documentation <https://help.github.com/>`_

- `GitHub pull request documentation
  <https://help.github.com/articles/using-pull-requests>`_

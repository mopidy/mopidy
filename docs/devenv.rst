.. _devenv:

***********************
Development environment
***********************

This page describes a common development setup for working with Mopidy and
Mopidy extensions. Of course, there may be other ways that work better for you
and the tools you use, but here's one recommended way to do it.

.. contents::
   :local:


Initial setup
=============

The following steps help you get a good initial setup. They build on each other
to some degree, so if you're not very familiar with Python development it might
be wise to proceed in the order laid out here.

.. contents::
   :local:


Install Mopidy the regular way
------------------------------

Install Mopidy the regular way. Mopidy has some non-Python dependencies which
may be tricky to install. Thus we recommend to always start with a full regular
Mopidy install, as described in :ref:`installation`. That is, if you're running
e.g. Debian, start with installing Mopidy from Debian packages.


Make a development workspace
----------------------------

Make a directory to be used as a workspace for all your Mopidy development::

    mkdir ~/mopidy-dev

It will contain all the Git repositories you'll check out when working on
Mopidy and extensions.


Make a virtualenv
-----------------

Make a Python `virtualenv <https://virtualenv.pypa.io/>`_ for Mopidy
development. The virtualenv will wall off Mopidy and its dependencies from the
rest of your system. All development and installation of Python dependencies,
versions of Mopidy, and extensions are done inside the virtualenv. This way
your regular Mopidy install, which you set up in the first step, is unaffected
by your hacking and will always be working.

Most of us use the `virtualenvwrapper
<https://virtualenvwrapper.readthedocs.org/>`_ to ease working with
virtualenvs, so that's what we'll be using for the examples here. First,
install and setup virtualenvwrapper as described in their docs.

To create a virtualenv named ``mopidy`` which uses Python 2.7, allows access to
system-wide packages like GStreamer, and uses the Mopidy workspace directory as
the "project path", run::

    mkvirtualenv -a ~/mopidy-dev --python `which python2.7` \
      --system-site-packages mopidy

Now, each time you open a terminal and want to activate the ``mopidy``
virtualenv, run::

    workon mopidy

This will both activate the ``mopidy`` virtualenv, and change the current
working directory to ``~/mopidy-dev``.


Clone the repo from GitHub
--------------------------

Once inside the virtualenv, it's time to clone the ``mopidy/mopidy`` Git repo
from GitHub::

    git clone https://github.com/mopidy/mopidy.git

When you've cloned the ``mopidy`` Git repo, ``cd`` into it::

    cd ~/mopidy-dev/mopidy/

With a fresh clone of the Git repo, you should start out on the ``develop``
branch. This is where all features for the next feature release land. To
confirm that you're on the right branch, run::

    git branch


Install development tools
-------------------------

We use a number of Python development tools. The :file:`dev-requirements.txt`
file has comments describing what we use each dependency for, so we might just
as well include the file verbatim here:

.. literalinclude:: ../dev-requirements.txt

Install them all into the active virtualenv by running `pip
<https://pip.pypa.io/>`_::

    pip install --upgrade -r dev-requirements.txt

To upgrade the tools in the future, just rerun the exact same command.


Install Mopidy from the Git repo
--------------------------------

Next up, we'll want to run Mopidy from the Git repo. There's two reasons for
this: first of all, it lets you easily change the source code, restart Mopidy,
and see the change take effect. Second, it's a convenient way to keep at the
bleeding edge, testing the latest developments in Mopidy itself or test some
extension against the latest Mopidy changes.

Assuming you're still inside the Git repo, use pip to install Mopidy from the
Git repo in an "editable" form::

    pip install --editable .

This will not copy the source code into the virtualenv's ``site-packages``
directory, but instead create a link there pointing to the Git repo. Using
``cdsitepackages`` from virtualenvwrapper, we can quickly show that the
installed :file:`Mopidy.egg-link` file points back to the Git repo::

    $ cdsitepackages
    $ cat Mopidy.egg-link
    /home/user/mopidy-dev/mopidy
    .%
    $

It will also create a ``mopidy`` executable inside the virtualenv that will
always run the latest code from the Git repo. Using another
virtualenvwrapper command, ``cdvirtualenv``, we can show that too::

    $ cdvirtualenv
    $ cat bin/mopidy
    ...

The executable should contain something like this, using :mod:`pkg_resources`
to look up Mopidy's "console script" entry point::

    #!/home/user/virtualenvs/mopidy/bin/python2
    # EASY-INSTALL-ENTRY-SCRIPT: 'Mopidy==0.19.5','console_scripts','mopidy'
    __requires__ = 'Mopidy==0.19.5'
    import sys
    from pkg_resources import load_entry_point

    if __name__ == '__main__':
        sys.exit(
            load_entry_point('Mopidy==0.19.5', 'console_scripts', 'mopidy')()
        )

.. note::

    It still works to run ``python mopidy`` directly on the
    :file:`~/mopidy-dev/mopidy/mopidy/` Python package directory, but if
    you don't run the ``pip install`` command above, the extensions bundled
    with Mopidy will not be registered with :mod:`pkg_resources`, making Mopidy
    quite useless.

Third, the ``pip install`` command will register the bundled Mopidy
extensions so that Mopidy may find them through :mod:`pkg_resources`. The
result of this can be seen in the Git repo, in a new directory called
:file:`Mopidy.egg-info`, which is ignored by Git. The
:file:`Mopidy.egg-info/entry_points.txt` file is of special interest as it
shows both how the above executable and the bundled extensions are connected to
the Mopidy source code:

.. code-block:: ini

    [console_scripts]
    mopidy = mopidy.__main__:main

    [mopidy.ext]
    http = mopidy.http:Extension
    local = mopidy.local:Extension
    mpd = mopidy.mpd:Extension
    softwaremixer = mopidy.softwaremixer:Extension
    stream = mopidy.stream:Extension

.. warning::

   It's not uncommon to clean up in the Git repo now and then, e.g. by running
   ``git clean``.

   If you do this, then the :file:`Mopidy.egg-info` directory will be removed,
   and :mod:`pkg_resources` will no longer know how to locate the "console
   script" entry point or the bundled Mopidy extensions.

   The fix is simply to run the install command again::

       pip install --editable .

Finally, we can go back to the workspace, again using a virtualenvwrapper
tool::

   cdproject


.. _running-from-git:

Running Mopidy from Git
=======================

As long as the virtualenv is activated, you can start Mopidy from any
directory. Simply run::

    mopidy

To stop it again, press :kbd:`Ctrl+C`.

Every time you change code in Mopidy or an extension and want to see it
live, you must restart Mopidy.

If you want to iterate quickly while developing, it may sound a bit tedious to
restart Mopidy for every minor change. Then it's useful to have tests to
exercise your code...


.. _running-tests:

Running tests
=============

Mopidy has quite good test coverage, and we would like all new code going into
Mopidy to come with tests.

.. contents::
   :local:


Test it all
-----------

You need to know at least one command; the one that runs all the tests::

    tox

This will run exactly the same tests as `Travis CI
<https://travis-ci.org/mopidy/mopidy>`_ runs for all our branches and pull
requests. If this command turns green, you can be quite confident that your
pull request will get the green flag from Travis as well, which is a
requirement for it to be merged.

As this is the ultimate test command, it's also the one taking the most time to
run; up to a minute, depending on your system. But, if you have patience, this
is all you need to know. Always run this command before pushing your changes to
GitHub.

If you take a look at the tox config file, :file:`tox.ini`, you'll see that tox
runs tests in multiple environments, including a ``flake8`` environment that
lints the source code for issues and a ``docs`` environment that tests that the
documentation can be built. You can also limit tox to just test specific
environments using the ``-e`` option, e.g. to run just unit tests::

    tox -e py27

To learn more, see the `tox documentation <http://tox.readthedocs.org/>`_ .


Running unit tests
------------------

Under the hood, ``tox -e py27`` will use `pytest <http://pytest.org/>`_ as the
test runner. We can also use it directly to run all tests::

    py.test

py.test has lots of possibilities, so you'll have to dive into their docs and
plugins to get full benefit from it. To get you interested, here are some
examples.

We can limit to just tests in a single directory to save time::

    py.test tests/http/

With the help of the pytest-xdist plugin, we can run tests with four Python
processes in parallel, which usually cuts the test time in half or more::

    py.test -n 4

Another useful feature from pytest-xdist, is the possiblity to stop on the
first test failure, watch the file system for changes, and then rerun the
tests. This makes for a very quick code-test cycle::

    py.test -f    # or --looponfail

With the help of the pytest-cov plugin, we can get a report on what parts of
the given module, ``mopidy`` in this example, are covered by the test suite::

    py.test --cov=mopidy --cov-report=term-missing

.. note::

    Up to date test coverage statistics can also be viewed online at
    `coveralls.io <https://coveralls.io/github/mopidy/mopidy>`_.

If we want to speed up the test suite, we can even get a list of the ten
slowest tests::

    py.test --durations=10

By now, you should be convinced that running py.test directly during
development can be very useful.


Continuous integration
----------------------

Mopidy uses the free service `Travis CI <https://travis-ci.org/mopidy/mopidy>`_
for automatically running the test suite when code is pushed to GitHub. This
works both for the main Mopidy repo, but also for any forks. This way, any
contributions to Mopidy through GitHub will automatically be tested by Travis
CI, and the build status will be visible in the GitHub pull request interface,
making it easier to evaluate the quality of pull requests.

For each successful build, Travis submits code coverage data to `coveralls.io
<https://coveralls.io/github/mopidy/mopidy>`_. If you're out of work, coveralls might
help you find areas in the code which could need better test coverage.


.. _code-linting:

Style checking and linting
--------------------------

We're quite pedantic about :ref:`codestyle` and try hard to keep the Mopidy
code base a very clean and nice place to work in.

Luckily, you can get very far by using the `flake8
<http://flake8.readthedocs.org/>`_ linter to check your code for issues before
submitting a pull request. Mopidy passes all of flake8's checks, with only a
very few exceptions configured in :file:`setup.cfg`. You can either run the
``flake8`` tox environment, like Travis CI will do on your pull request::

    tox -e flake8

Or you can run flake8 directly::

    flake8

If successful, the command will not print anything at all.

.. note::

    In some rare cases it doesn't make sense to listen to flake8's warnings. In
    those cases, ignore the check by appending ``# noqa: <warning code>`` to
    the source line that triggers the warning. The ``# noqa`` part will make
    flake8 skip all checks on the line, while the warning code will help other
    developers lookup what you are ignoring.


.. _writing-docs:

Writing documentation
=====================

To write documentation, we use `Sphinx <http://sphinx-doc.org/>`_. See their
site for lots of documentation on how to use Sphinx.

.. note::

    To generate a few graphs which are part of the documentation, you need some
    additional dependencies. You can install them from APT with::

        sudo apt-get install python-pygraphviz graphviz

To build the documentation, go into the :file:`docs/` directory::

    cd ~/mopidy-dev/mopidy/docs/

Then, to see all available build targets, run::

    make

To generate an HTML version of the documentation, run::

    make html

The generated HTML will be available at :file:`_build/html/index.html`. To open
it in a browser you can run either of the following commands, depending on your
OS::

    xdg-open _build/html/index.html    # Linux
    open _build/html/index.html        # OS X

The documentation at https://docs.mopidy.com/ is hosted by `Read the Docs
<https://readthedocs.org/>`_, which automatically updates the documentation
when a change is pushed to the ``mopidy/mopidy`` repo at GitHub.


Working on extensions
=====================

Much of the above also applies to Mopidy extensions, though they're often a bit
simpler. They don't have documentation sites and their test suites are either
small and fast, or sadly missing entirely. Most of them use tox and flake8, and
py.test can be used to run their test suites.

.. contents::
   :local:


Installing extensions
---------------------

As always, the ``mopidy`` virtualenv should be active when working on
extensions::

    workon mopidy

Just like with non-development Mopidy installations, you can install extensions
using pip::

    pip install Mopidy-Scrobbler

Installing an extension from its Git repo works the same way as with Mopidy
itself. First, go to the Mopidy workspace::

    cdproject    # or cd ~/mopidy-dev/

Clone the desired Mopidy extension::

    git clone https://github.com/mopidy/mopidy-spotify.git

Change to the newly created extension directory::

    cd mopidy-spotify/

Then, install the extension in "editable" mode, so that it can be imported from
anywhere inside the virtualenv and the extension is registered and discoverable
through :mod:`pkg_resources`::

    pip install --editable .

Every extension will have a ``README.rst`` file. It may contain information
about extra dependencies required, development process, etc. Extensions usually
have a changelog in the readme file.


Upgrading extensions
--------------------

Extensions often have a much quicker life cycle than Mopidy itself, often with
daily releases in periods of active development. To find outdated extensions in
your virtualenv, you can run::

    pip search mopidy

This will list all available Mopidy extensions and compare the installed
versions with the latest available ones.

To upgrade an extension installed with pip, simply use pip::

    pip install --upgrade Mopidy-Scrobbler

To upgrade an extension installed from a Git repo, it's usually enough to pull
the new changes in::

    cd ~/mopidy-dev/mopidy-spotify/
    git pull

Of course, if you have local modifications, you'll need to stash these away on
a branch or similar first.

Depending on the changes to the extension, it may be necessary to update the
metadata about the extension package by installing it in "editable" mode
again::

    pip install --editable .


Contribution workflow
=====================

Before you being, make sure you've read the :ref:`contributing` page and the
guidelines there. This section will focus more on the practical workflow.

For the examples, we're making a change to Mopidy. Approximately the same
workflow should work for most Mopidy extensions too.

.. contents::
   :local:


Setting up Git remotes
----------------------

Assuming we already have a local Git clone of the upstream Git repo in
:file:`~/mopidy-dev/mopidy/`, we can run ``git remote -v`` to list the
configured remotes of the repo::

    $ git remote -v
    origin  https://github.com/mopidy/mopidy.git (fetch)
    origin  https://github.com/mopidy/mopidy.git (push)

For clarity, we can rename the ``origin`` remote to ``upstream``::

    $ git remote rename origin upstream
    $ git remote -v
    upstream        https://github.com/mopidy/mopidy.git (fetch)
    upstream        https://github.com/mopidy/mopidy.git (push)

If you haven't already, `fork the repository
<https://help.github.com/articles/fork-a-repo/>`_ to your own GitHub account.

Then, add the new fork as a remote to your local clone::

    git remote add myuser git@github.com:myuser/mopidy.git

The end result is that you have both the upstream repo and your own fork as
remotes::

    $ git remote -v
    myuser  git@github.com:myuser/mopidy.git (fetch)
    myuser  git@github.com:myuser/mopidy.git (push)
    upstream        https://github.com/mopidy/mopidy.git (fetch)
    upstream        https://github.com/mopidy/mopidy.git (push)


Creating a branch
-----------------

Fetch the latest data from all remotes without affecting your working
directory::

    git remote update

Now, we are ready to create and checkout a new branch off of the upstream
``develop`` branch for our work::

    git checkout -b fix/666-crash-on-foo upstream/develop

Do the work, while remembering to adhere to code style, test the changes, make
necessary updates to the documentation, and making small commits with good
commit messages. All as described in :ref:`contributing` and elsewhere in
the :ref:`devenv` guide.


Creating a pull request
-----------------------

When everything is done and committed, push the branch to your fork on GitHub::

    git push myuser fix/666-crash-on-foo

Go to the repository on GitHub where you want the change merged, in this case
https://github.com/mopidy/mopidy, and `create a pull request
<https://help.github.com/articles/creating-a-pull-request/>`_.


Updating a pull request
-----------------------

When the pull request is created, `Travis CI
<https://travis-ci.org/mopidy/mopidy>`__ will run all tests on it. If something
fails, you'll get notified by email. You might as well just fix the issues
right away, as we won't merge a pull request without a green Travis build. See
:ref:`running-tests` on how to run the same tests locally as Travis CI runs on
your pull request.

When you've fixed the issues, you can update the pull request simply by pushing
more commits to the same branch in your fork::

    git push myuser fix/666-crash-on-foo

Likewise, when you get review comments from other developers on your pull
request, you're expected to create additional commits which addresses the
comments. Push them to your branch so that the pull request is updated.

.. note::

    Setup the remote as the default push target for your branch::

        git branch --set-upstream-to myuser/fix/666-crash-on-foo

    Then you can push more commits without specifying the remote::

        git push

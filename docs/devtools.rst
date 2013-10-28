*****************
Development tools
*****************

Here you'll find description of the development tools we use.


Continuous integration
======================

Mopidy uses the free service `Travis CI <https://travis-ci.org/mopidy/mopidy>`_
for automatically running the test suite when code is pushed to GitHub. This
works both for the main Mopidy repo, but also for any forks. This way, any
contributions to Mopidy through GitHub will automatically be tested by Travis
CI, and the build status will be visible in the GitHub pull request interface,
making it easier to evaluate the quality of pull requests.

In addition, we run a Jenkins CI server at http://ci.mopidy.com/ that runs all
test on multiple platforms (Ubuntu, OS X, x86, arm) for every commit we push to
the ``develop`` branch in the main Mopidy repo on GitHub. Thus, new code isn't
tested by Jenkins before it is merged into the ``develop`` branch, which is a
bit late, but good enough to get broad testing before new code is released.

In addition to running tests, the Jenkins CI server also gathers coverage
statistics and uses flake8 to check for errors and possible improvements in our
code. So, if you're out of work, the code coverage and flake8 data at the CI
server should give you a place to start.


Protocol debugger
=================

Since the main interface provided to Mopidy is through the MPD protocol, it is
crucial that we try and stay in sync with protocol developments. In an attempt
to make it easier to debug differences Mopidy and MPD protocol handling we have
created ``tools/debug-proxy.py``.

This tool is proxy that sits in front of two MPD protocol aware servers and
sends all requests to both, returning the primary response to the client and
then printing any diff in the two responses.

Note that this tool depends on ``gevent`` unlike the rest of Mopidy at the time
of writing. See :option:`tools/debug-proxy.py --help` for available options.
Sample session::

    [127.0.0.1]:59714
    listallinfo
    --- Reference response
    +++ Actual response
    @@ -1,16 +1,1 @@
    -file: uri1
    -Time: 4
    -Artist: artist1
    -Title: track1
    -Album: album1
    -file: uri2
    -Time: 4
    -Artist: artist2
    -Title: track2
    -Album: album2
    -file: uri3
    -Time: 4
    -Artist: artist3
    -Title: track3
    -Album: album3
    -OK
    +ACK [2@0] {listallinfo} incorrect arguments

To ensure that Mopidy and MPD have comparable state it is suggested you setup
both to use ``tests/data/advanced_tag_cache`` for their tag cache and
``tests/data/scanner/advanced/`` for the music folder and ``tests/data`` for
playlists.


Documentation writing
=====================

To write documentation, we use `Sphinx <http://sphinx-doc.org/>`_. See their
site for lots of documentation on how to use Sphinx. To generate HTML from the
documentation files, you need some additional dependencies.

You can install them through Debian/Ubuntu package management::

    sudo apt-get install python-sphinx python-pygraphviz graphviz

Then, to generate docs::

    cd docs/
    make        # For help on available targets
    make html   # To generate HTML docs

The documentation at http://docs.mopidy.com/ is automatically updated when a
documentation update is pushed to ``mopidy/mopidy`` at GitHub.


Creating releases
=================

#. Update changelog and commit it.

#. Bump the version number in ``mopidy/__init__.py``. Remember to update the
   test case in ``tests/version_test.py``.

#. Merge the release branch (``develop`` in the example) into master::

    git checkout master
    git merge --no-ff -m "Release v0.16.0" develop

#. Build package and test it manually in a new virtualenv. The following
   assumes the use of virtualenvwrapper::

    python setup.py sdist
    mktmpenv
    pip install path/to/dist/Mopidy-0.16.0.tar.gz
    toggleglobalsitepackages

   Then test Mopidy manually to confirm that the package is working correctly.

#. Tag the release::

    git tag -a -m "Release v0.16.0" v0.16.0

#. Push to GitHub::

    git push
    git push --tags

#. Build source package and upload to PyPI::

    python setup.py sdist upload

#. Build wheel package and upload to PyPI::

    pip install -U wheel
    python setup.py bdist_wheel upload

#. Merge ``master`` back into ``develop`` and push the branch to GitHub.

#. Make sure the new tag is built by Read the Docs, and that the ``latest``
   version shows the newly released version.

#. Spread the word through the topic on #mopidy on IRC, @mopidy on Twitter, and
   on the mailing list.

#. Update the Debian package.


Updating Debian packages
========================

This howto is not intended to learn you all the details, just to give someone
already familiar with Debian packaging an overview of how Mopidy's Debian
packages is maintained.

#. Install the basic packaging tools::

       sudo apt-get install build-essential git-buildpackage

#. Check out the ``debian`` branch of the repo::

       git checkout -t origin/debian
       git pull

#. Merge the latest release tag into the ``debian`` branch::

       git merge v0.16.0

#. Update the ``debian/changelog`` with a "New upstream release" entry::

       dch -v 0.16.0-0mopidy1
       git add debian/changelog
       git commit -m "debian: New upstream release"

#. Check if any dependencies in ``debian/control`` or similar needs updating.

#. Install any Build-Deps listed in ``debian/control``.

#. Build the package and fix any issues repeatedly until the build succeeds and
   the Lintian check at the end of the build is satisfactory::

       git buildpackage -uc -us

#. Install and test newly built package::

       sudo debi

#. If everything is OK, build the package a final time to tag the package
   version::

       git buildpackage -uc -us --git-tag

#. Push the changes you've done to the ``debian`` branch and the new tag::

       git push
       git push --tags

#. If you're building for multiple architectures, checkout the ``debian``
   branch on the other builders and run::

       git buildpackage -uc -us

#. Copy files to the APT server. Make sure to select the correct part of the
   repo, e.g. main, contrib, or non-free::

       scp ../mopidy*_0.16* bonobo.mopidy.com:/srv/apt.mopidy.com/app/incoming/stable/main

#. Update the APT repo::

       ssh bonobo.mopidy.com
       /srv/apt.mopidy.com/app/update.sh

#. Test installation from apt.mopidy.com::

       sudo apt-get update
       sudo apt-get dist-upgrade

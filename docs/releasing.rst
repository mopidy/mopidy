******************
Release procedures
******************

Here we try to keep an up to date record of how Mopidy releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.


Creating releases
=================

#. Update changelog and commit it.

#. Bump the version number in ``mopidy/__init__.py``. Remember to update the
   test case in ``tests/test_version.py``.

#. Merge the release branch (``develop`` in the example) into master::

    git checkout master
    git merge --no-ff -m "Release v0.16.0" develop

#. Install/upgrade tools used for packaging::

    pip install -U twine wheel

#. Build package and test it manually in a new virtualenv. The following
   assumes the use of virtualenvwrapper::

    python setup.py sdist bdist_wheel

    mktmpenv
    pip install path/to/dist/Mopidy-0.16.0.tar.gz
    toggleglobalsitepackages
    # do manual test
    deactivate

    mktmpenv
    pip install path/to/dist/Mopidy-0.16.0-py27-none-any.whl
    toggleglobalsitepackages
    # do manual test
    deactivate

#. Tag the release::

    git tag -a -m "Release v0.16.0" v0.16.0

#. Push to GitHub::

    git push
    git push --tags

#. Upload the previously built and tested sdist and bdist_wheel packages to
   PyPI::

    twine upload dist/Mopidy-0.16.0*

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

#. Create a Wheezy pbuilder env if running on Ubuntu and this the first time.
   See :issue:`561` for details about why this is needed::

       DIST=wheezy sudo git-pbuilder update --mirror=http://mirror.rackspace.com/debian/ --debootstrapopts --keyring=/usr/share/keyrings/debian-archive-keyring.gpg

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

   If you are using the pbuilder make sure this command is::

       sudo git buildpackage -uc -us --git-ignore-new --git-pbuilder --git-dist=wheezy --git-no-pbuilder-autoconf

#. Install and test newly built package::

       sudo debi

   Again for pbuilder use::

       sudo debi --debs-dir /var/cache/pbuilder/result/

#. If everything is OK, build the package a final time to tag the package
   version::

       git buildpackage -uc -us --git-tag

   Pbuilder::

       sudo git buildpackage -uc -us --git-ignore-new --git-pbuilder --git-dist=wheezy --git-no-pbuilder-autoconf --git-tag

#. Push the changes you've done to the ``debian`` branch and the new tag::

       git push
       git push --tags

#. If you're building for multiple architectures, checkout the ``debian``
   branch on the other builders and run::

       git buildpackage -uc -us

   Modify as above to use the pbuilder as needed.

#. Copy files to the APT server. Make sure to select the correct part of the
   repo, e.g. main, contrib, or non-free::

       scp ../mopidy*_0.16* bonobo.mopidy.com:/srv/apt.mopidy.com/app/incoming/stable/main

#. Update the APT repo::

       ssh bonobo.mopidy.com
       /srv/apt.mopidy.com/app/update.sh

#. Test installation from apt.mopidy.com::

       sudo apt-get update
       sudo apt-get dist-upgrade

******************
Release procedures
******************

Here we try to keep an up to date record of how Mopidy releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

.. _creating-releases:

Creating releases
=================

#. Update changelog and commit it.

#. Bump the version number in ``mopidy/__init__.py``.

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

    git push --follow-tags

#. Upload the previously built and tested sdist and bdist_wheel packages to
   PyPI::

    twine upload dist/Mopidy-0.16.0*

#. Merge ``master`` back into ``develop`` and push the branch to GitHub.

#. Make sure the new tag is built by Read the Docs, and that the ``latest``
   version shows the newly released version.

#. Spread the word through the topic on #mopidy on IRC, @mopidy on Twitter, and
   on the mailing list.

#. Notify distribution packagers, including but not limited to: Debian, Arch
   Linux, Homebrew.

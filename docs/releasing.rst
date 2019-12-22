.. _creating-releases:

******************
Release procedures
******************

Here we try to keep an up to date record of how Mopidy releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

#. Update the changelog. Commit it.

#. Bump the version number in ``setup.cfg``. Commit it.

#. Merge the release branch (``develop`` in the example) into master::

    git checkout master
    git pull
    git merge --no-ff -m "Release v3.0.0" develop

#. Install/upgrade tools used for packaging::

    python3 -m pip install --upgrade twine wheel

#. Build package and test it manually in a new virtualenv. The following
   assumes the use of virtualenvwrapper::

    python setup.py sdist bdist_wheel

    mktmpenv
    pip install ~/mopidy-dev/mopidy/dist/Mopidy-3.0.0.tar.gz
    toggleglobalsitepackages
    # do manual test
    deactivate

    mktmpenv
    pip install ~/mopidy-dev/mopidy/dist/Mopidy-3.0.0-py3-none-any.whl
    toggleglobalsitepackages
    # do manual test
    deactivate

#. Tag the release::

    git tag -a -m "Release v3.0.0" v3.0.0

#. Push to GitHub::

    git push --follow-tags

#. Upload the previously built and tested sdist and bdist_wheel packages to
   PyPI::

    twine upload dist/Mopidy-3.0.0.tar.gz dist/Mopidy-3.0.0-py3-none-any.whl

#. Merge ``master`` back into ``develop`` and push the branch to GitHub.

#. Make sure the new tag is built by Read the Docs, and that the ``latest``
   version shows the newly released version.

#. Spread the word through an announcement post on the `Discourse forum
   <https://discourse.mopidy.com/>`_.

#. Notify distribution packagers, including but not limited to:
   Debian, Arch Linux, Homebrew.

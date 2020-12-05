.. _creating-releases:

******************
Release procedures
******************

Here we try to keep an up to date record of how Mopidy releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.


Releasing extensions
====================

Extensions that are maintained in the Mopidy organization use a quite
stream-lined release procedure.

#. Make sure that everything has been merged into the `master` branch on
   GitHub, and that all CI checks are green.

#. Make any manual tests you feel is required.

#. Bump version in `setup.cfg`, to e.g. `2.0.2`.

#. Commit the bumped version::

    git commit -m "Release v2.0.2"

#. Tag the commit::

    git tag -m "Release v2.0.2" v2.0.2

   It is encouraged to use ``-s`` to sign the tag if you have a GnuPG setup.

#. Push to GitHub::

    git push origin master --follow-tags

#. Go to the GitHub repository's tags page, e.g.
   ``https://github.com/mopidy/mopidy-foo/tags``. Find the tag and select
   "Create release" in the tag's dropdown menu.

#. Copy the tag, e.g. ``v2.0.2`` into the "title" field. Write a changelog
   entry in the description field, and hit "Release".

#. GitHub Actions now builds the package and uploads it to PyPI.

This procedure has several benefits:

- Everyone with commit access can make releases.
- None without direct PyPI access can make releases without also leaving the
  source code of what they released publicly available on GitHub, creating an
  audit log in case of any malicious deeds.
- The changelog can be amended post-release through the GitHub Releases UI.

The primary drawback of this procedure is that there is no obvious way to
maintain a changelog in-between releases. The preferred solution is to make
releases often, so that writing up the changelog from the recent Git commits is
done in a minute or two.


How to setup this release workflow
----------------------------------

If you maintain a Mopidy extension, you're encouraged to adopt the same
procedure.

To setup this on your own repo, you must:

#. Copy
`.github/workflows/release.yml` from the Mopidy `cookiecutter project
<https://github.com/mopidy/cookiecutter-mopidy-ext/blob/master/%7B%7Bcookiecutter.repo_name%7D%7D/.github/workflows/release.yml>`_.

#. Create a token in your account settings at PyPI with access to the relevant
   PyPI package.

#. Copy the token to a new secret called ``PYPI_TOKEN`` in your GitHub repo's
   settings.

With the ``release.yml`` file and the ``PYPI_TOKEN`` secret in place, releases
should automatically be uploaded to PyPI when you follow the procedure above.


Releasing Mopidy itself
=======================

Mopidy itself is a bit more complicated than extensions because the changelog
is maintained in the Git repo, and because we maintain multiple branches to be
able to work towards the next bugfix release and the next feature release at
the same time.


Preparations
------------

#. Update the changelog. Commit and push it.

#. Make sure that everything has been merged into the `master` branch on
   GitHub, and that all CI checks are green.

#. Make any manual tests you feel is required.


Release
-------

#. Merge the release branch (``develop`` in the example) into ``master``::

    git checkout master
    git pull
    git merge --no-ff -m "Release v3.3.0" develop

#. Bump version in `setup.cfg`, to e.g. `2.0.2`, and set the release date in
   the changelog.

#. Commit the bumped version::

    git commit -m "Release v3.3.0"

#. Install/upgrade tools used for packaging::

    python3 -m pip install --upgrade twine wheel

#. Build package::

    python3 setup.py sdist bdist_wheel

#. Tag the commit::

    git tag -m "Release v3.3.0" v3.3.0

   It is encouraged to use ``-s`` to sign the tag if you have a GnuPG setup.

#. Push to GitHub::

    git push origin master --follow-tags

#. Upload the packages to PyPI::

    twine upload dist/Mopidy-2.0.2.tar.gz dist/Mopidy-2.0.2-py3-none-any.whl


Post-release
------------

#. Merge ``master`` back into ``develop`` and push the branch to GitHub::

    git checkout develop
    git merge master
    git push origin develop

#. Make sure the new tag is built by Read the Docs, and that the ``latest``
   version shows the newly released version.

#. Spread the word through an announcement post on the `Discourse forum
   <https://discourse.mopidy.com/>`_.

#. Notify distribution packagers, including but not limited to:
   Debian, Arch Linux, Homebrew.

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

#. Make sure that everything has been merged into the ``master`` branch on
   GitHub, and that all CI checks are green.

#. Perform any manual tests you feel are required.

#. Bump the version in ``setup.cfg`` in line with :ref:`our strategy <versioning>`.
   For example, to ``2.0.2``.

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
   entry in the description field, and hit "Publish release".

#. GitHub Actions now builds the package and uploads it to PyPI.

This procedure has several benefits:

- Everyone with commit access can make releases.
- No one, except those with direct PyPI access, can make releases without
  also leaving the source code of what they released publicly available on
  GitHub, creating an audit log in case of any malicious actions.
- The changelog can be amended post-release through the GitHub Releases UI.

The primary drawback of this procedure is that there is no obvious way to
maintain a changelog in-between releases. The preferred solution is to make
releases often, so that writing up a changelog from the recent Git commits is
done in a minute or two.


How to setup this release workflow
----------------------------------

If you maintain a Mopidy extension, you're encouraged to adopt the same
procedure.

To setup this on your own repo, you must:

#. Copy ``.github/workflows/release.yml`` from the Mopidy
   `cookiecutter project
   <https://github.com/mopidy/cookiecutter-mopidy-ext/blob/master/%7B%7Bcookiecutter.repo_name%7D%7D/.github/workflows/release.yml>`_.

#. Create an API token in your account settings at PyPI with scope to access
   the extension's PyPI package.

#. Copy the token to a new secret called ``PYPI_TOKEN`` in your GitHub repo's
   settings. Ignore the section titled "Using this token" on PyPI.

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

#. Make sure that everything has been merged into the ``develop`` branch on
   GitHub, and that all CI checks are green.

#. Perform any manual tests you feel are required.


Release
-------

#. Bump the version in ``setup.cfg`` in line with :ref:`our strategy <versioning>`.
   For example, to ``3.3.0``, and set the release date in the changelog.

#. Commit the bumped version and release date::

    git commit -m "Prepare release of v3.3.0"

#. Merge the release branch (``develop`` in the example) into ``master``::

    git checkout master
    git pull
    git merge --no-ff -m "Release v3.3.0" develop

#. Tag the commit::

    git tag -m "Release v3.3.0" v3.3.0

   It is encouraged to use ``-s`` to sign the tag if you have a GnuPG setup.

#. Push to GitHub::

    git push origin master --follow-tags

#. Go to the GitHub repository's tags page at
   ``https://github.com/mopidy/mopidy/tags``. Find the tag and select
   "Create release" in the tag's dropdown menu.

#. Copy the tag, e.g. ``v3.3.0`` into the "title" field. Write a changelog
   entry in the description field, and hit "Publish release".

#. GitHub Actions now builds the package and uploads it to PyPI.


Post-release
------------

#. To prepare for further development, merge the ``master`` branch back into
   the ``develop`` branch and push it to GitHub::

    git checkout develop
    git merge master
    git push origin develop

#. Make sure the new tag is built by
   `Read the Docs <https://readthedocs.org/projects/mopidy/builds/>`_,
   and that the `"latest" version <https://docs.mopidy.com/en/latest/>`_
   shows the newly released version.

#. Spread the word through an announcement post on the `Discourse forum
   <https://discourse.mopidy.com/>`_.

#. Notify distribution packagers, including but not limited to:

   - `Arch Linux <https://www.archlinux.org/packages/community/any/mopidy/>`_
   - `Debian <https://salsa.debian.org/mopidy-team>`_
   - `Homebrew <https://github.com/mopidy/homebrew-mopidy>`_

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

#. Make sure that everything has been merged into the ``main`` branch on
   GitHub, and that all CI checks are green.

#. Perform any manual tests you feel are required.

#. Bump the version in ``setup.cfg`` in line with :ref:`our strategy <versioning>`.
   For example, to ``2.0.2``.

#. Commit the bumped version::

    git commit -m "Release v2.0.2"

#. Tag the commit with an annotated tag::

    git tag -a -m "Release v2.0.2" v2.0.2

   It is encouraged to use ``-s`` to sign the tag if you have a GnuPG setup.

#. Push to GitHub::

    git push origin main --follow-tags

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
   <https://github.com/mopidy/cookiecutter-mopidy-ext/blob/main/%7B%7Bcookiecutter.repo_name%7D%7D/.github/workflows/release.yml>`_.

#. Create an API token in your account settings at PyPI with scope to access
   the extension's PyPI package.

#. Copy the token to a new secret called ``PYPI_TOKEN`` in your GitHub repo's
   settings. Ignore the section titled "Using this token" on PyPI.

With the ``release.yml`` file and the ``PYPI_TOKEN`` secret in place, releases
should automatically be uploaded to PyPI when you follow the procedure above.


Releasing Mopidy itself
=======================

Mopidy itself is a bit more complicated than extensions because the changelog
is maintained in the Git repo.


Preparations
------------

#. Make sure that everything has been merged into the ``main`` branch on
   GitHub, and that all CI checks are green.

#. Make sure the changelog in the ``docs/changelog.rst`` file includes all
   significant changes since the last release. Commit and push it.

#. Perform any manual tests you feel are required.


Release
-------

#. Select a version number in line with :ref:`our strategy <versioning>`,
   e.g. ``v3.3.0`` in the following examples.

#. Update the release in ``docs/changelog.rst`` with the right version number
   and release date.

#. Commit the final touches to the changelog::

    git commit -m "Release v3.3.0"

#. Tag the commit with an annotated tag::

    git tag -a -m "Release v3.3.0" v3.3.0

   It is encouraged to use ``-s`` to sign the tag if you have a GnuPG setup.

#. Verify that Mopidy reports the new version number::

     mopidy --version

    If it doesn't, check that you've properly tagged the release.

#. Push to GitHub::

    git push origin main --follow-tags

#. Go to the GitHub repository's
   `tags page <https://github.com/mopidy/mopidy/tags>`_.
   Find the tag and select "Create release" in the tag's dropdown menu.

#. Copy the tag, e.g. ``v3.3.0`` into the "title" field. Write a changelog
   entry in the description field, and hit "Publish release".

#. GitHub Actions now builds the package and uploads it to PyPI.


Post-release
------------

#. Make sure the new tag is built by
   `Read the Docs <https://readthedocs.org/projects/mopidy/builds/>`_,
   and that the `"stable" version <https://docs.mopidy.com/stable/>`_
   shows the newly released version.

#. Spread the word through an announcement post on the `Discourse forum
   <https://discourse.mopidy.com/>`_.

#. Notify distribution packagers, including but not limited to:

   - `Arch Linux <https://archlinux.org/packages/extra/any/mopidy/>`_
   - `Debian <https://salsa.debian.org/mopidy-team>`_
   - `Homebrew <https://github.com/mopidy/homebrew-mopidy>`_

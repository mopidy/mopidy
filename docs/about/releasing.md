
# Release procedures

Here we try to keep an up to date record of how Mopidy releases are made. This
documentation serves both as a checklist, to reduce the project's dependency on
key individuals, and as a stepping stone to more automation.

## Releasing extensions

Extensions that are maintained in the Mopidy organization use a quite
stream-lined release procedure.

1. Make sure that everything has been merged into the `main` branch on
   GitHub, and that all CI checks are green.

1. Perform any manual tests you feel are required.

1. Go to the GitHub repository's releases page, e.g.
   `https://github.com/mopidy/mopidy-foo/releases`.

1. In the "choose a tag" dropdown, create a new tag, e.g. `v0.1.0`.

1. Add a title, e.g. `v0.1.0`, and a description of the changes.

1. Decide if the release is a pre-release (alpha, beta, or release candidate) or
   should be marked as the latest release, and click "Publish release".

1. Once the release is created, the `release.yml` GitHub Actions workflow builds
   the package and uploads it to PyPI.

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

### How to setup this release workflow

If you maintain a Mopidy extension, you're encouraged to adopt the same
procedure.

See the [extension project template](https://github.com/mopidy/mopidy-ext-template/)
and specifically the generated project's README for further instructions.

## Releasing Mopidy itself

Mopidy itself is a bit more complicated than extensions because the changelog
is maintained in the Git repo.

### Preparations

- Make sure that everything has been merged into the `main` branch on
  GitHub, and that all CI checks are green.

- Make sure the changelog in the `docs/changelog/index.md` file includes all
  significant changes since the last release. Commit and push it.

- Perform any manual tests you feel are required.

### Release

1. Select a version number in line with [our strategy](../about/versioning.md).

1. Update the release in `docs/changelog/index.md` with the right version number
   and release date. Commit and push it.

1. Release the new version exactly like you would do for an extension, with the
   addition of linking from the release to the changelog entry in the docs.

### Post-release

- Make sure the new tag is built by
  [Read the Docs](https://app.readthedocs.org/projects/mopidy/),
  and that the ["stable" version](https://docs.mopidy.com/stable/)
  shows the newly released version.

- Spread the word through an announcement post on the [Discourse
  forum](https://discourse.mopidy.com/).

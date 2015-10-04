# Mopidy

## Table of Contents
* [Mopidy](#mopidy)
    * [What is Mopidy?](#intro)
    * [Development process](#development-process)
        * [Contributing](#contributing)
            * [Helping users](#helping-users)
            * [Issue guidelines](#issue-guidelines)
            * [Pull Requests](#pull-requests)
        * [Releases](#releases)

<div id='intro'/>
## What is Mopidy?

Mopidy is an extensible music server written in Python which plays music from local disk (vanilla) or Spotify, SoundCloud, Google Play Music and other cloud servers through the use of extensions.
It runs on Linux computers or Macs that have a network connectivity and audio output.

Since it is just a server (an [MPD](http://www.musicpd.org) and HTTP server to be exact), additional frontends need to be used in other to control Mopidy.
The playlist can be edited from any phone, tablet, or computer using a range of [MPD](https://docs.mopidy.com/en/latest/clients/mpd/) and [web clients](https://docs.mopidy.com/en/latest/ext/web/#ext-web).

## Development Process

### Contributing

#### Helping Users

Considered as the best way to contribute to Mopidy, helping other users is highly appreciated as it frees up development time from contributors.

A great place to start is by joining both IRC (*#mopidy* at [irc.freenode.net](irc.freenode.net)) and the [discussion forum](discuss.mopidy.com) and answering questions from users in need of help.

#### Issue Guidelines

Another valuable contribution is filing an issue in the [issue tracker](https://github.com/mopidy/mopidy/issues) for any bugs found or features wanted. If the issue already exists, helping reproduce the bugs or flesh out the new feature is also welcomed.

#### Pull Requests

Code contributions are made mainly by [Github's Pull Request feature](https://help.github.com/articles/using-pull-requests) and they should follow some guidelines:

1. A new branch, based on the `develop` branch, should be created for every feature or bug fix. Branches should be kept small and on topic, as that makes them far easier to review. The naming convetions for branches are as follows:
    * Features get the prefix `feature/` e.g. `feature/track-last-modified-as-ms`
    * Bug fixes get the prefix `fix/` e.g. `fix/902-consume-track-on-next`
    * Improvements to the documentation get the prefix `docs/` e.g. `docs/add-ext-mopidy-spotify-tunigo`

2. The [code style](https://docs.mopidy.com/en/latest/codestyle/#codestyle) must be followed and the [flake8](https://flake8.readthedocs.org/en/2.4.1/) linter must not show any warnings as [Travis CI](https://travis-ci.org/) will check.

3. Tests must be included for any new feature or substantial bug fix.

4. Documentation must also be included for any new feature.

5. Send a pull request to the `develop` branch.

### Releases

After the changelog is commited and the version bumped, the `develop` branch is merged into the `master` branch, a tag is created and the Debian package is updated.

The news about a new release are spread through the Mopidy IRC, Twitter and mailing list so that all the package maintainers from different distributions can update their respective package and make it easily available to install for the end user.

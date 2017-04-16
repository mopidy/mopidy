# Mopidy

## Table of Contents
* [Mopidy](#mopidy)
    * [What is Mopidy?](#intro)
    * [Development process](#development-process)
        * [Methodologies](#methodologies)
        * [Contributing](#contributing)
            * [Helping users](#helping-users)
            * [Issue guidelines](#issue-guidelines)
            * [Pull Requests](#pull-requests)
        * [Releases](#releases)
          * [Versioning](#versioning)
          * [Schedule](#schedule)
          * [Procedure](#procedure)
    * [Sponsors](#sponsors)

<div id='intro'/>
## What is Mopidy?

Mopidy is an extensible music server written in Python which plays music from local disk (vanilla) or Spotify, SoundCloud, Google Play Music and other cloud servers through the use of extensions.
It runs on Linux computers or Macs that have a network connectivity and audio output.

Since it is just a server (an [MPD](http://www.musicpd.org) and HTTP server to be exact), additional frontends need to be used in other to control Mopidy.
The playlist can be edited from any phone, tablet, or computer using a range of [MPD](https://docs.mopidy.com/en/latest/clients/mpd/) and [web clients](https://docs.mopidy.com/en/latest/ext/web/#ext-web).

## Development Process

### Methodologies

We tried to get in contact with the owner and main contributor of the project [Stein Magnus Jodal](https://github.com/jodal) in order to get some insight into the development process and methods used during the development of the application.
Unfortunately, he didn't reply to our email yet.

A mix of [FDD(Feature-Driven Development)](https://en.wikipedia.org/wiki/Feature-driven_development) and TAD(Test-After Development) looks to be used as a framework to develop the application.
From the documentation available, it seems that progress is made when a certain feature is requested (or needed/wanted) and the job of implementing that feature is assigned to a contributor. This contributor must also include unit tests for the feature implemented before it is accepted in the code. This is all acomplished with the help of Github tools such as the [issue tracker](https://github.com/mopidy/mopidy/issues) for discussing features and [pull requests](https://github.com/mopidy/mopidy/pulls) for reviewing and accepting the implementation of those features.

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
#### Versioning
Mopidy follows [Semantic Versioning](http://semver.org/) which means that the version numbers have three parts, MAJOR.MINOR.PATCH.

Extensions should stay compatible throughout a major version but there's no promise they'll break on a major release (e.g. from 1.x to 2.x).
Every major release should be accompanied by a FAQ regarding big changes to the extensions API which extension developers can resort to.

#### Schedule
New features are intended to be released every month with bug fixes being released when the bugs in question are too serious to wait for the next feature release.

Bug fixes are only released for the latest feature release, which means that previous minor versions aren't supported as to not spread the limited resources.

#### Procedure

After the changelog is commited and the version bumped, the `develop` branch is merged into the `master` branch, a tag is created and the Debian package is updated.

The news about a new release are spread through the Mopidy IRC, Twitter and mailing list so that all the package maintainers from different distributions can update their respective package and make it easily available to install for the end user.

## Sponsors
#### Rackspace
<a href="http://www.rackspace.com">
<img src="./images/sponsors/rackspace.jpg" height="80"/>
</a>

Provides hosting services for free like the APT package repository, the Discourse forum and a mailing service.

#### Fastly
<a href="http://www.fastly.com">
<img src="./images/sponsors/fastly.png" height="80"/>
</a>

Provides a CDN service for free, accelerating requests to all the Mopidy services.

#### GlobalSign
<a href="http://www.globalsign.com">
<img src="./images/sponsors/globalsign.png" height="80"/>
</a>

Provides a freeSSL certificate for the website [mopidy.com](http://mopidy.com).










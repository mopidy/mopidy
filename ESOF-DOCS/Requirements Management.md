# Mopidy Requirements

## Table of contents
- [Mopidy Requirements](#mopidy-requirements)
    - [Introduction](#introduction)
    - [Requirements](#requirements)
        - [System Requirements](#system-requirements)
        - [Elicitation and Analysis](#elicitation-and-analysis)
        - [Specification](#specification)
        - [Validation](#validation)
        - [Use cases](#use-cases)
            - [Backends](#backends)
            - [Frontends](#frontends)
        - [Domain model](#domain-model)
        
## Introduction

Mopidy is an extensible music server written in Python which plays music from local disk.
It was made to be very customizable and extensible so that both the users and developers can shape it the way they want it.

The software was designed into various modules which accompanied with a good documentation makes it very easy to contribute to. It also makes use of a very laid back policy regarding new feature requests.

## Requirements

### System Requirements

Mopidy requires a Unix based system (for example a Linux distribution or a Macintosh) with network connectivity and audio output. It also needs Python to be installed on the system, although most distributions make use of a package manager for dealing with dependencies.

### Elicitation and Analysis

New features can be suggested essentially by everyone. The suggestions and discussions of these features take place in the [issue tracker](https://github.com/mopidy/mopidy/issues) of the Github repository, which later are merged upstream through the use of pull requests.

### Specification

Mopidy itself does not have a SRS (Software Requirements Specification) document, however, there are some other documents available which explain the inner workings of the software:
* [Glossary](https://mopidy.readthedocs.org/en/latest/glossary/)
* [Mopidy Command](https://mopidy.readthedocs.org/en/latest/command/)
* [API Reference](https://mopidy.readthedocs.org/en/latest/api/)
* [Module Reference](https://mopidy.readthedocs.org/en/latest/modules/)

### Validation

The development of this project is very informal and, as such, the release schedule as its discussion isn't very strict. The features that are acepted and added are a mix of what the developers think is most important/requested as well as features that they just find fun to make, even though they may only be of use for a very limited number of users.

Following a [Semantic Versioning](http://semver.org/)  every major release is accompanied by a FAQ regarding big changes to the extensions API which developers can resort to. 
Bugfixes are released whenever bugs are discovered and too serious to wait, though bugfix releases are not provided to older versions besides the newest to prevent the spread of the limited resources this project has.

### Use cases

Since Mopidy is just a music server in itself that plays music from local disk, it needs to be extended in order to be controlled or play music from other sources. This is done through the use of extensions.

Extensions can be of two types: a **backend** or **frontend**.
Both are installed seperately on top of Mopidy and they can extend the server's functionality in various ways.

In order for backends and frontends to communicate with each other Mopidy provides an API called `mopidy.core` which basically [makes multiple frontends capable of using multiple backends](https://mopidy.readthedocs.org/en/latest/glossary/#term-core).

<img src="./images/uml/mopidy.png" width="600" />

#### Backends

The main purpose of a backend is to provide Mopidy of more sources of music, increasing its library size.

One of the backends that comes installed with vanilla Mopidy is [Mopidy-Local](https://mopidy.readthedocs.org/en/latest/ext/local/) which is responsible for getting music files from the local disk.
However, backends for online music services can be easily added, provided they have a public API available.
Some of the existing backends are:
[Mopidy-Spotify](https://github.com/mopidy/mopidy-spotify),
[Mopidy-SoundCloud](https://github.com/mopidy/mopidy-soundcloud),
[Mopidy-YouTube](https://github.com/dz0ny/mopidy-youtube), etc.

<img src="./images/uml/backend.png" width="600" />

#### Frontends

Frontends on the other hand are what make it possible to control the server itself using the `mopidy.core` API which provides enough functionality to create for example (but not limited to) music players.
Frontends can also be web based, making it possible to control Mopidy remotely ([Android clients](http://mopidy.readthedocs.org/en/latest/clients/mpd/#mpd-android-clients), [Web clients](http://mopidy.readthedocs.org/en/latest/clients/mpd/#mpd-web-clients)).

<img src="./images/uml/core.png" width="600" />

#### Domain model

<img src="./images/uml/domainmodel.png" width=“600” />

## Glossary

* Frontend - Exposes Mopidy to the external world , it can implement protocols like HTTP , MPD and MPRIS and serves to send the requests to the core.

* Core - It combines the responses into a single response to the requesting frontend. Which is to say that it's responsible for making possible multiple frontends use multiple backends, being able to control the tracklist,playlist,library,playback and history.

* Mixer - By default it uses Audio to control volume and muting in software but there are alternative implementations that typically are independent of the Audio .

* Backend - It integrates the music sources providing all the requests made by the frontend ,it also uses Audio to provide playback independently of the backend of choice.

* Audio - It's a playback provider using parts of the GStreamer library although there is the possibility to implement different playback providers.





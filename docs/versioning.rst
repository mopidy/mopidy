.. _versioning:

**********
Versioning
**********

Mopidy follows `Semantic Versioning <http://semver.org/>`_. In summary this
means that our version numbers have three parts, MAJOR.MINOR.PATCH, which
change according to the following rules:

- When we *make incompatible API changes*, we increase the MAJOR number.

- When we *add features* in a backwards-compatible manner, we increase the
  MINOR number.

- When we *fix bugs* in a backwards-compatible manner, we increase the PATCH
  number.

The promise is that if you make a Mopidy extension for Mopidy 1.0, it should
work unchanged with any Mopidy 1.x release, but probably not with 2.0. When a
new major version is released, you must review the incompatible changes and
update your extension accordingly.


Release schedule
================

We intend to have about one feature release every month in periods of active
development. The features added is a mix of what we feel is most
important/requested of the missing features, and features we develop just
because we find them fun to make, even though they may be useful for very few
users or for a limited use case.

Bugfix releases will be released whenever we discover bugs that are too serious
to wait for the next feature release. We will only release bugfix releases for
the last feature release. E.g. when 1.2.0 is released, we will no longer
provide bugfix releases for the 1.1.x series. In other words, there will be just
a single supported release at any point in time. This is to not spread our
limited resources too thin.

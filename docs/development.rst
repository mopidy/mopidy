***********
Development
***********

Development of Mopidy is coordinated through the IRC channel ``#mopidy`` at
``irc.freenode.net`` and through `GitHub <http://github.com/>`_.


Release schedule
================

We intend to have about one timeboxed feature release every month
in periods of active development. The feature releases are numbered 0.x.0. The
features added is a mix of what we feel is most important/requested of the
missing features, and features we develop just because we find them fun to
make, even though they may be useful for very few users or for a limited use
case.

Bugfix releases, numbered 0.x.y, will be released whenever we discover bugs
that are too serious to wait for the next feature release. We will only release
bugfix releases for the last feature release. E.g. when 0.3.0 is released, we
will no longer provide bugfix releases for the 0.2 series. In other words,
there will be just a single supported release at any point in time.


Feature wishlist
================

We maintain our collection of sane or less sane ideas for future Mopidy
features as `issues <https://github.com/mopidy/mopidy/issues>`_ at GitHub
labeled with `the "wishlist" label
<https://github.com/mopidy/mopidy/issues?labels=wishlist>`_. Feel free to vote
up any feature you would love to see in Mopidy, but please refrain from adding
a comment just to say "I want this too!". You are of course free to add
comments if you have suggestions for how the feature should work or be
implemented, and you may add new wishlist issues if your ideas are not already
represented.


Code style
==========

- Follow :pep:`8` unless otherwise noted. `pep8.py
  <http://pypi.python.org/pypi/pep8/>`_ can be used to check your code against
  the guidelines, however remember that matching the style of the surrounding
  code is also important.

- Use four spaces for indentation, *never* tabs.

- Use CamelCase with initial caps for class names::

      ClassNameWithCamelCase

- Use underscore to split variable, function and method names for
  readability. Don't use CamelCase.

  ::

      lower_case_with_underscores

- Use the fact that empty strings, lists and tuples are :class:`False` and
  don't compare boolean values using ``==`` and ``!=``.

- Follow whitespace rules as described in :pep:`8`. Good examples::

      spam(ham[1], {eggs: 2})
      spam(1)
      dict['key'] = list[index]

- Limit lines to 80 characters and avoid trailing whitespace. However note that
  wrapped lines should be *one* indentation level in from level above, except
  for ``if``, ``for``, ``with``, and ``while`` lines which should have two
  levels of indentation::

      if (foo and bar ...
              baz and foobar):
          a = 1

      from foobar import (foo, bar, ...
          baz)

- For consistency, prefer ``'`` over ``"`` for strings, unless the string
  contains ``'``.

- Take a look at :pep:`20` for a nice peek into a general mindset useful for
  Python coding.


Commit guidelines
=================

- We follow the development process described at http://nvie.com/git-model.

- Keep commits small and on topic.

- If a commit looks too big you should be working in a feature branch not a
  single commit.

- Merge feature branches with ``--no-ff`` to keep track of the merge.


Running tests
=============

To run tests, you need a couple of dependencies. They can be installed through
Debian/Ubuntu package management::

    sudo apt-get install python-coverage python-mock python-nose

Or, they can be installed using ``pip``::

    sudo pip install -r requirements/tests.txt

Then, to run all tests, go to the project directory and run::

    nosetests

For example::

    $ nosetests
    ......................................................................
    ......................................................................
    ......................................................................
    .......
    ----------------------------------------------------------------------
    Ran 217 tests in 0.267s

    OK

To run tests with test coverage statistics::

    nosetests --with-coverage

For more documentation on testing, check out the `nose documentation
<http://somethingaboutorange.com/mrl/projects/nose/>`_.


Continuous integration
======================

Mopidy uses the free service `Travis CI <http://travis-ci.org/#mopidy/mopidy>`_
for automatically running the test suite when code is pushed to GitHub. This
works both for the main Mopidy repo, but also for any forks. This way, any
contributions to Mopidy through GitHub will automatically be tested by Travis
CI, and the build status will be visible in the GitHub pull request interface,
making it easier to evaluate the quality of pull requests.

In addition, we run a Jenkins CI server at http://ci.mopidy.com/ that runs all
test on multiple platforms (Ubuntu, OS X, x86, arm) for every commit we push to
the ``develop`` branch in the main Mopidy repo on GitHub. Thus, new code isn't
tested by Jenkins before it is merged into the ``develop`` branch, which is a
bit late, but good enough to get broad testing before new code is released.

In addition to running tests, the Jenkins CI server also gathers coverage
statistics and uses pylint to check for errors and possible improvements in our
code. So, if you're out of work, the code coverage and pylint data at the CI
server should give you a place to start.


Protocol debugging
==================

Since the main interface provided to Mopidy is through the MPD protocol, it is
crucial that we try and stay in sync with protocol developments. In an attempt
to make it easier to debug differences Mopidy and MPD protocol handling we have
created ``tools/debug-proxy.py``.

This tool is proxy that sits in front of two MPD protocol aware servers and
sends all requests to both, returning the primary response to the client and
then printing any diff in the two responses.

Note that this tool depends on ``gevent`` unlike the rest of Mopidy at the time
of writing. See ``--help`` for available options. Sample session::

    [127.0.0.1]:59714
    listallinfo
    --- Reference response
    +++ Actual response
    @@ -1,16 +1,1 @@
    -file: uri1
    -Time: 4
    -Artist: artist1
    -Title: track1
    -Album: album1
    -file: uri2
    -Time: 4
    -Artist: artist2
    -Title: track2
    -Album: album2
    -file: uri3
    -Time: 4
    -Artist: artist3
    -Title: track3
    -Album: album3
    -OK
    +ACK [2@0] {listallinfo} incorrect arguments

To ensure that Mopidy and MPD have comparable state it is suggested you setup
both to use ``tests/data/advanced_tag_cache`` for their tag cache and
``tests/data/scanner/advanced/`` for the music folder and ``tests/data`` for
playlists.


Writing documentation
=====================

To write documentation, we use `Sphinx <http://sphinx.pocoo.org/>`_. See their
site for lots of documentation on how to use Sphinx. To generate HTML or LaTeX
from the documentation files, you need some additional dependencies.

You can install them through Debian/Ubuntu package management::

    sudo apt-get install python-sphinx python-pygraphviz graphviz

Then, to generate docs::

    cd docs/
    make        # For help on available targets
    make html   # To generate HTML docs

The documentation at http://docs.mopidy.com/ is automatically updated when a
documentation update is pushed to ``mopidy/mopidy`` at GitHub.


Creating releases
=================

#. Update changelog and commit it.

#. Merge the release branch (``develop`` in the example) into master::

    git checkout master
    git merge --no-ff -m "Release v0.2.0" develop

#. Tag the release::

    git tag -a -m "Release v0.2.0" v0.2.0

#. Push to GitHub::

    git push
    git push --tags

#. Build package and upload to PyPI::

    rm MANIFEST                         # Will be regenerated by setup.py
    python setup.py sdist upload

#. Spread the word.


Setting profiles during development
===================================

While developing Mopidy switching settings back and forth can become an all too
frequent occurrence. As a quick hack to get around this you can structure your
settings file in the following way::

    import os
    profile = os.environ.get('PROFILE', '').split(',')

    if 'spotify' in profile:
        BACKENDS = (u'mopidy.backends.spotify.SpotifyBackend',)
    elif 'local' in profile:
        BACKENDS = (u'mopidy.backends.local.LocalBackend',)
        LOCAL_MUSIC_PATH = u'~/music'

    if 'shoutcast' in profile:
        OUTPUT = u'lame ! shout2send mount="/stream"'
    elif 'silent' in profile:
        OUTPUT = u'fakesink'
        MIXER = None

    SPOTIFY_USERNAME = u'xxxxx'
    SPOTIFY_PASSWORD = u'xxxxx'

Using this setup you can now run Mopidy with ``PROFILE=silent,spotify mopidy``
if you for instance want to test Spotify without any actual audio output.

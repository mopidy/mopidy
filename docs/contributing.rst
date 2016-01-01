.. _contributing:

************
Contributing
************

If you want to contribute to Mopidy, here are some tips to get you started.


.. _asking-questions:

Asking questions
================

Please get in touch with us in one of these ways when requesting help with
Mopidy and its extensions:

- Our discussion forum: `discuss.mopidy.com <https://discuss.mopidy.com>`_.
  Just sign in and fire away.

- Our IRC channel: `#mopidy <https://webchat.freenode.net/?channels=#mopidy>`_
  on `irc.freenode.net <http://freenode.net>`_,
  with public `searchable logs <https://botbot.me/freenode/mopidy/>`_. Be
  prepared to hang around for a while, as we're not always around to answer
  straight away.

Before asking for help, it might be worth your time to read the
:ref:`troubleshooting` page, both so you might find a solution to your problem
but also to be able to provide useful details when asking for help.


Helping users
=============

If you want to contribute to Mopidy, a great place to start is by helping other
users on IRC and in the discussion forum. This is a contribution we value
highly. As more people help with user support, new users get faster and better
help. For your own benefit, you'll quickly learn what users find confusing,
difficult or lacking, giving you some ideas for where you may contribute
improvements, either to code or documentation. Lastly, this may also free up
time for other contributors to spend more time on fixing bugs or implementing
new features.


.. _issue-guidelines:

Issue guidelines
================

#. If you need help, see :ref:`asking-questions` above. The GitHub issue
   tracker is not a support forum.

#. If you are not sure if what you're experiencing is a bug or not, post in the
   `discussion forum <https://discuss.mopidy.com>`__ first to verify that it's
   a bug.

#. If you are sure that you've found a bug or have a feature request, check if
   there's already an issue in the `issue tracker
   <https://github.com/mopidy/mopidy/issues>`_. If there is, see if there is
   anything you can add to help reproduce or fix the issue.

#. If there is no exising issue matching your bug or feature request, create a
   `new issue <https://github.com/mopidy/mopidy/issues/new>`_. Please include
   as much relevant information as possible. If it's a bug, including how to
   reproduce the bug and any relevant logs or error messages.


Pull request guidelines
=======================

#. Before spending any time on making a pull request:

   - If it's a bug, :ref:`file an issue <issue-guidelines>`.

   - If it's an enhancement, discuss it with other Mopidy developers first,
     either in a GitHub issue, on the discussion forum, or on IRC. Making sure
     your ideas and solutions are aligned with other contributors greatly
     increases the odds of your pull request being quickly accepted.

#. Create a new branch, based on the ``develop`` branch, for every feature or
   bug fix. Keep branches small and on topic, as that makes them far easier to
   review. We often use the following naming convention for branches:

   - Features get the prefix ``feature/``, e.g.
     ``feature/track-last-modified-as-ms``.

   - Bug fixes get the prefix ``fix/``, e.g. ``fix/902-consume-track-on-next``.

   - Improvements to the documentation get the prefix ``docs/``, e.g.
     ``docs/add-ext-mopidy-spotify-tunigo``.

#. Follow the :ref:`code style <codestyle>`, especially make sure the
   ``flake8`` linter does not complain about anything. Travis CI will check
   that your pull request is "flake8 clean". See :ref:`code-linting`.

#. Include tests for any new feature or substantial bug fix. See
   :ref:`running-tests`.

#. Include documentation for any new feature. See :ref:`writing-docs`.

#. Feel free to include a changelog entry in your pull request. The changelog
   is in :file:`docs/changelog.rst`.

#. Write good commit messages.

   - Follow the template "topic: description" for the first line of the commit
     message, e.g. "mpd: Switch list command to using list_distinct". See the
     commit history for inspiration.

   - Use the rest of the commit message to explain anything you feel isn't
     obvious. It's better to have the details here than in the pull request
     description, since the commit message will live forever.

   - Write in the imperative, present tense: "add" not "added".

   For more inspiration, feel free to read these blog posts:

   - `Writing Git commit messages
     <http://365git.tumblr.com/post/3308646748/writing-git-commit-messages>`_

   - `A Note About Git Commit Messages
     <http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html>`_

   - `On commit messages
     <http://who-t.blogspot.ch/2009/12/on-commit-messages.html>`_

#. Send a pull request to the ``develop`` branch. See the `GitHub pull request
   docs <https://help.github.com/articles/using-pull-requests>`_ for help.

.. note::

    If you are contributing a bug fix for a specific minor version of Mopidy
    you should create the branch based on ``release-x.y`` instead of
    ``develop``. When the release is done the changes will be merged back into
    ``develop`` automatically as part of the normal release process. See
    :ref:`creating-releases`.

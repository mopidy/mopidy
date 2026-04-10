
# Contributing

If you want to contribute to Mopidy, here are some tips to get you started.

## Asking questions

Please get in touch with us in one of these ways when requesting help with
Mopidy and its extensions:

- Our Discourse forum: [discourse.mopidy.com](https://discourse.mopidy.com).

- The `#mopidy-users` stream on Zulip chat: [mopidy.zulipchat.com](https://mopidy.zulipchat.com).

Before asking for help, it might be worth your time to read the
[troubleshooting](../usage/troubleshooting.md) page, both so you might find a
solution to your problem but also to be able to provide useful details when
asking for help.

## Helping users

If you want to contribute to Mopidy, a great place to start is by helping other
users in the discussion forum and the `#mopidy-users` Zulip stream. This is a
contribution we value highly. As more people help with user support, new users
get faster and better help. For your own benefit, you'll quickly learn what
users find confusing, difficult or lacking, giving you some ideas for where you
may contribute improvements, either to code or documentation. Lastly, this may
also free up time for other contributors to spend more time on fixing bugs or
implementing new features.

## Issue guidelines

- If you need help, see [Asking questions](#asking-questions) above. The GitHub
  issue tracker is not a support forum.

- If you are not sure if what you're experiencing is a bug or not, post in the
  [discussion forum](https://discourse.mopidy.com) first to verify that
  it's a bug.

- If you are sure that you've found a bug or have a feature request, check if
  there's already an issue in the [issue tracker](https://github.com/mopidy/mopidy/issues).
  If there is, see if there is anything you can add to help reproduce or fix
  the issue.

- If there is no existing issue matching your bug or feature request, create a
  [new issue](https://github.com/mopidy/mopidy/issues/new). Please include
  as much relevant information as possible. If it's a bug, include how to
  reproduce the bug and any relevant logs or error messages.

## Pull request guidelines

- Before spending any time on making a pull request:

    - If it's a bug, [file an issue](#issue-guidelines).

    - If it's an enhancement, discuss it with other Mopidy developers first,
      either in a GitHub issue, on the discussion forum, or on Zulip chat.
      Making sure your ideas and solutions are aligned with other contributors
      greatly increases the odds of your pull request being quickly accepted.

- Create a new branch, based on the `main` branch, for every feature or
  bug fix. Keep branches small and on topic, as that makes them far easier to
  review.

- Follow the [code style](codestyle.md), especially make sure the
  `ruff` linter does not complain about anything. Our CI setup will
  check that your pull request is "ruff clean". See [code linting](devenv.md#style-checking-and-linting).

- Include tests for any new feature or substantial bug fix. See
  [running tests](devenv.md#running-tests).

- Include documentation for any new feature. See [writing docs](devenv.md#writing-documentation).

- Feel free to include a changelog entry in your pull request. The changelog
  is in `docs/changelog/index.md`.

- Write good commit messages.

    - Follow the template "topic: description" for the first line of the commit
      message, e.g. "mpd: Switch list command to using list_distinct". See the
      commit history for inspiration.

    - Use the rest of the commit message to explain anything you feel isn't
      obvious. It's better to have the details here than in the pull request
      description, since the commit message will live forever.

    - Write in the imperative, present tense: "add" not "added".

    For more inspiration, feel free to read these blog posts:

    - [Writing Git commit messages](https://365git.tumblr.com/post/3308646748/writing-git-commit-messages)

    - [A Note About Git Commit Messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)

    - [On commit messages](https://who-t.blogspot.com/2009/12/on-commit-messages.html)

- Send a pull request to the `main` branch. See the [GitHub pull request docs](https://help.github.com/en/articles/about-pull-requests) for help.

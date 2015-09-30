# Primeiro relatorio

### Development process

[*Link from docs here*](https://docs.mopidy.com/en/latest/contributing/)

- Uses IRC and a [forum](discuss.mopidy.com) for Q&A, discussions and helping users
- Helping others is considered a very good way to contribute as there is usually high demand for help which consumes development time from contributors
- Relies on **issue tracker** from github for *bug reports* and *feature requests*
- PR's are the main way to contribute to the project and have a very strict guideline

#### How are PR handled

1. Before spending any time on making a pull request:


  * If it’s a bug, file an issue.

  * If it’s an enhancement, discuss it with other Mopidy developers first, either in a GitHub issue, on the discussion forum, or on IRC. Making sure your ideas and solutions are aligned with other contributors greatly increases the odds of your pull request being quickly accepted.

2. Create a new branch, based on the develop branch, for every feature or bug fix. Keep branches small and on topic, as that makes them far easier to review. We often use the following naming convention for branches:

    * Features get the prefix feature/, e.g. feature/track-last-modified-as-ms.

    * Bug fixes get the prefix fix/, e.g. fix/902-consume-track-on-next.

    * Improvements to the documentation get the prefix docs/, e.g. docs/add-ext-mopidy-spotify-tunigo.

3. Follow the code style, especially make sure the flake8 linter does not complain about anything. Travis CI will check that your pull request is “flake8 clean”. See Style checking and linting.

4. Include tests for any new feature or substantial bug fix. See Running tests.

5. Include documentation for any new feature. See Writing documentation.

6. Feel free to include a changelog entry in your pull request. The changelog is in docs/changelog.rst.

7. Write good commit messages.

    * Follow the template “topic: description” for the first line of the commit message, e.g. “mpd: Switch list command to using list_distinct”. See the commit history for inspiration.

    * Use the rest of the commit message to explain anything you feel isn’t obvious. It’s better to have the details here than in the pull request description, since the commit message will live forever.

    * Write in the imperative, present tense: “add” not “added”.

8. Send a pull request to the develop branch. See the GitHub pull request docs for help.

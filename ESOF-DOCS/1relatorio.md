# First Report

### Introduction
Mopidy is an extensible music server written in Python.

Mopidy plays music from local disk, Spotify, SoundCloud, Google Play Music, and more. You edit the playlist from any phone, tablet, or computer using a range of MPD and web clients.

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

### Development Environment
To contribute to the development of Mopidy,first follow the instructions to install a regular install of Mopidy, then continue with reading Contributing and Development environment.
The following steps help you get a good initial setup. 

1. Install Mopidy the regular way, the installation depends upon your OS and/or distribution, if you’re running e.g. Debian, start with installing Mopidy from Debian packages.

2. Make a development workspace
   >mkdir ~/mopidy-dev
   It will contain all the Git repositories you’ll check out when working on Mopidy and extensions.
 
3. Make a virtualenv, is a tool to create isolated Python environments.
   The virtualenv will wall off Mopidy and its dependencies from the rest of your system. All development and installation of Python dependencies, versions of Mopidy, and extensions are done inside the virtualenv.
   Most of us use the virtualenvwrapper to ease working with virtualenvs,
   P.S: SEE HOW TO INSTALL VIRTUALENVWRAPPER
   To create a virtualenv:
   >mkvirtualenv -a ~/mopidy-dev --python `which python2.7` \
   --system-site-packages mopidy
   Now, each time you open a terminal and want to activate the mopidy virtualenv, run:
   >workon mopidy

4. Clone the repo from GitHub
   >git clone https://github.com/mopidy/mopidy.git
   >cd ~/mopidy-dev/mopidy/

5. Install development tools
   We use a number of Python development tools. The dev-requirements.txt file has comments describing what we use each dependency for
   Install them all into the active virtualenv by running pip:
   >pip install --upgrade -r dev-requirements.txt
   To upgrade the tools in the future, just rerun the exact same command.

6. Install Mopidy from the Git repo
   we’ll want to run Mopidy from the Git repo. There’s two reasons for this: first of all, it lets you easily change the source code, restart Mopidy, and see the change take effect. Second, it’s a convenient way to keep at the bleeding edge, testing the latest developments in Mopidy itself or test some extension against the latest Mopidy changes.
   Assuming you’re still inside the Git repo, use pip to install Mopidy from the Git repo in an “editable” form:
   >pip install --editable .

>#####Warning
>It’s not uncommon to clean up in the Git repo now and then, e.g. by running git clean.

If you do this, then the Mopidy.egg-info directory will be removed, and pkg_resources will no longer know how to locate the “console script” entry point or the bundled Mopidy extensions.

The fix is simply to run the install command again:
>pip install --editable .

Finally, we can go back to the workspace, again using a virtualenvwrapper tool:
>cdproject

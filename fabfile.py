from fabric.api import execute, local, settings, task


@task
def docs():
    local('make -C docs/ html')


@task
def autodocs():
    auto(docs)


@task
def test(path=None):
    path = path or 'tests/'
    local('nosetests ' + path)


@task
def autotest(path=None):
    auto(test, path=path)


@task
def coverage(path=None):
    path = path or 'tests/'
    local(
        'nosetests --with-coverage --cover-package=mopidy '
        '--cover-branches --cover-html ' + path)


@task
def autocoverage(path=None):
    auto(coverage, path=path)


@task
def lint(path=None):
    path = path or '.'
    local('flake8 $(find %s -iname "*.py")' % path)


@task
def autolint(path=None):
    auto(lint, path=path)


def auto(task, *args, **kwargs):
    while True:
        local('clear')
        with settings(warn_only=True):
            execute(task, *args, **kwargs)
        local(
            'inotifywait -q -e create -e modify -e delete '
            '--exclude ".*\.(pyc|sw.)" -r docs/ mopidy/ tests/')


@task
def update_authors():
    # Keep authors in the order of appearance and use awk to filter out dupes
    local(
        "git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS")

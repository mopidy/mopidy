import sys

from invoke import run, task


@task
def docs(ctx, watch=False, warn=False):
    if watch:
        return watcher(docs)
    run('make -C docs/ html', warn=warn)


@task
def test(ctx, path=None, coverage=False, watch=False, warn=False):
    if watch:
        return watcher(test, path=path, coverage=coverage)
    path = path or 'tests/'
    cmd = 'pytest'
    if coverage:
        cmd += ' --cov=mopidy --cov-report=term-missing'
    cmd += ' %s' % path
    run(cmd, pty=True, warn=warn)


@task
def lint(ctx, watch=False, warn=False):
    if watch:
        return watcher(lint)
    run('flake8', warn=warn)


@task
def update_authors(ctx):
    # Keep authors in the order of appearance and use awk to filter out dupes
    run("git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS")


def watcher(task, *args, **kwargs):
    while True:
        run('clear')
        kwargs['warn'] = True
        task(*args, **kwargs)
        try:
            run(
                r'inotifywait -q -e create -e modify -e delete '
                r'--exclude ".*\.(pyc|sw.)" -r docs/ mopidy/ tests/')
        except KeyboardInterrupt:
            sys.exit()

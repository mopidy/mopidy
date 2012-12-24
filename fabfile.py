from fabric.api import local


def test(path=None):
    path = path or 'tests/'
    local('nosetests ' + path)


def autotest(path=None):
    while True:
        local('clear')
        test(path)
        local(
            'inotifywait -q -e create -e modify -e delete '
            '--exclude ".*\.(pyc|sw.)" -r mopidy/ tests/')


def update_authors():
    # Keep authors in the order of appearance and use awk to filter out dupes
    local(
        "git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS")

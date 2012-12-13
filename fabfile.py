from fabric.api import local


def test():
    local('nosetests tests/')


def autotest():
    while True:
        local('clear')
        test()
        local(
            'inotifywait -q -e create -e modify -e delete '
            '--exclude ".*\.(pyc|sw.)" -r mopidy/ tests/')


def update_authors():
    # Keep authors in the order of appearance and use awk to filter out dupes
    local(
        "git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS")

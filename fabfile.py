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

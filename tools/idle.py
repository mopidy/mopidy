#! /usr/bin/env python

# This script is helper to systematicly test the behaviour of MPD's idle
# command. It is simply provided as a quick hack, expect nothing more.

from __future__ import unicode_literals

import logging
import pprint
import socket

host = ''
port = 6601

url = "13 - a-ha - White Canvas.mp3"
artist = "a-ha"

data = {'id': None, 'id2': None, 'url': url, 'artist': artist}

# Commands to run before test requests to coerce MPD into right state
setup_requests = [
    'clear',
    'add "%(url)s"',
    'add "%(url)s"',
    'add "%(url)s"',
    'play',
    #'pause',  # Uncomment to test paused idle behaviour
    #'stop',  # Uncomment to test stopped idle behaviour
]

# List of commands to test for idle behaviour. Ordering of list is important in
# order to keep MPD state as intended. Commands that are obviously
# informational only or "harmfull" have been excluded.
test_requests = [
    'add "%(url)s"',
    'addid "%(url)s" "1"',
    'clear',
    #'clearerror',
    #'close',
    #'commands',
    'consume "1"',
    'consume "0"',
    # 'count',
    'crossfade "1"',
    'crossfade "0"',
    #'currentsong',
    #'delete "1:2"',
    'delete "0"',
    'deleteid "%(id)s"',
    'disableoutput "0"',
    'enableoutput "0"',
    #'find',
    #'findadd "artist" "%(artist)s"',
    #'idle',
    #'kill',
    #'list',
    #'listall',
    #'listallinfo',
    #'listplaylist',
    #'listplaylistinfo',
    #'listplaylists',
    #'lsinfo',
    'move "0:1" "2"',
    'move "0" "1"',
    'moveid "%(id)s" "1"',
    'next',
    #'notcommands',
    #'outputs',
    #'password',
    'pause',
    #'ping',
    'play',
    'playid "%(id)s"',
    #'playlist',
    'playlistadd "foo" "%(url)s"',
    'playlistclear "foo"',
    'playlistadd "foo" "%(url)s"',
    'playlistdelete "foo" "0"',
    #'playlistfind',
    #'playlistid',
    #'playlistinfo',
    'playlistadd "foo" "%(url)s"',
    'playlistadd "foo" "%(url)s"',
    'playlistmove "foo" "0" "1"',
    #'playlistsearch',
    #'plchanges',
    #'plchangesposid',
    'previous',
    'random "1"',
    'random "0"',
    'rm "bar"',
    'rename "foo" "bar"',
    'repeat "0"',
    'rm "bar"',
    'save "bar"',
    'load "bar"',
    #'search',
    'seek "1" "10"',
    'seekid "%(id)s" "10"',
    #'setvol "10"',
    'shuffle',
    'shuffle "0:1"',
    'single "1"',
    'single "0"',
    #'stats',
    #'status',
    'stop',
    'swap "1" "2"',
    'swapid "%(id)s" "%(id2)s"',
    #'tagtypes',
    #'update',
    #'urlhandlers',
    #'volume',
]


def create_socketfile():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.settimeout(0.5)
    fd = sock.makefile('rw', 1)  # 1 = line buffered
    fd.readline()  # Read banner
    return fd


def wait(fd, prefix=None, collect=None):
    while True:
        line = fd.readline().rstrip()
        if prefix:
            logging.debug('%s: %s', prefix, repr(line))
        if line.split()[0] in ('OK', 'ACK'):
            break


def collect_ids(fd):
    fd.write('playlistinfo\n')

    ids = []
    while True:
        line = fd.readline()
        if line.split()[0] == 'OK':
            break
        if line.split()[0] == 'Id:':
            ids.append(line.split()[1])
    return ids


def main():
    subsystems = {}

    command = create_socketfile()

    for test in test_requests:
        # Remove any old ids
        del data['id']
        del data['id2']

        # Run setup code to force MPD into known state
        for setup in setup_requests:
            command.write(setup % data + '\n')
            wait(command)

        data['id'], data['id2'] = collect_ids(command)[:2]

        # This connection needs to be make after setup commands are done or
        # else they will cause idle events.
        idle = create_socketfile()

        # Wait for new idle events
        idle.write('idle\n')

        test = test % data

        logging.debug('idle: %s', repr('idle'))
        logging.debug('command: %s', repr(test))

        command.write(test + '\n')
        wait(command, prefix='command')

        while True:
            try:
                line = idle.readline().rstrip()
            except socket.timeout:
                # Abort try if we time out.
                idle.write('noidle\n')
                break

            logging.debug('idle: %s', repr(line))

            if line == 'OK':
                break

            request_type = test.split()[0]
            subsystem = line.split()[1]
            subsystems.setdefault(request_type, set()).add(subsystem)

        logging.debug('---')

    pprint.pprint(subsystems)


if __name__ == '__main__':
    main()

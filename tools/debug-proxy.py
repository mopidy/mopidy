#! /usr/bin/env python

from __future__ import unicode_literals

import argparse
import difflib
import sys

from gevent import select, server, socket

COLORS = ['\033[1;%dm' % (30 + i) for i in range(8)]
BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE = COLORS
RESET = "\033[0m"
BOLD = "\033[1m"


def proxy(client, address, reference_address, actual_address):
    """Main handler code that gets called for each connection."""
    client.setblocking(False)

    reference = connect(reference_address)
    actual = connect(actual_address)

    if reference and actual:
        loop(client, address, reference, actual)
    else:
        print 'Could not connect to one of the backends.'

    for sock in (client, reference, actual):
        close(sock)


def connect(address):
    """Connect to given address and set socket non blocking."""
    try:
        sock = socket.socket()
        sock.connect(address)
        sock.setblocking(False)
    except socket.error:
        return None
    return sock


def close(sock):
    """Shutdown and close our sockets."""
    try:
        sock.shutdown(socket.SHUT_WR)
        sock.close()
    except socket.error:
        pass


def loop(client, address, reference, actual):
    """Loop that handles one MPD reqeust/response pair per iteration."""

    # Consume banners from backends
    responses = dict()
    disconnected = read(
        [reference, actual], responses, find_response_end_token)
    diff(address, '', responses[reference], responses[actual])

    # We lost a backend, might as well give up.
    if disconnected:
        return

    client.sendall(responses[reference])

    while True:
        responses = dict()

        # Get the command from the client. Not sure how an if this will handle
        # client sending multiple commands currently :/
        disconnected = read([client], responses, find_request_end_token)

        # We lost the client, might as well give up.
        if disconnected:
            return

        # Send the entire command to both backends.
        reference.sendall(responses[client])
        actual.sendall(responses[client])

        # Get the entire resonse from both backends.
        disconnected = read(
            [reference, actual], responses, find_response_end_token)

        # Send the client the complete reference response
        client.sendall(responses[reference])

        # Compare our responses
        diff(address,
             responses[client], responses[reference], responses[actual])

        # Give up if we lost a backend.
        if disconnected:
            return


def read(sockets, responses, find_end_token):
    """Keep reading from sockets until they disconnet or we find our token."""

    # This function doesn't go to well with idle when backends are out of sync.
    disconnected = False

    for sock in sockets:
        responses.setdefault(sock, '')

    while sockets:
        for sock in select.select(sockets, [], [])[0]:
            data = sock.recv(4096)
            responses[sock] += data

            if find_end_token(responses[sock]):
                sockets.remove(sock)

            if not data:
                sockets.remove(sock)
                disconnected = True

    return disconnected


def find_response_end_token(data):
    """Find token that indicates the response is over."""
    for line in data.splitlines(True):
        if line.startswith(('OK', 'ACK')) and line.endswith('\n'):
            return True
    return False


def find_request_end_token(data):
    """Find token that indicates that request is over."""
    lines = data.splitlines(True)
    if not lines:
        return False
    elif 'command_list_ok_begin' == lines[0].strip():
        return 'command_list_end' == lines[-1].strip()
    else:
        return lines[0].endswith('\n')


def diff(address, command, reference_response, actual_response):
    """Print command from client and a unified diff of the responses."""
    sys.stdout.write('[%s]:%s\n%s' % (address[0], address[1], command))
    for line in difflib.unified_diff(reference_response.splitlines(True),
                                     actual_response.splitlines(True),
                                     fromfile='Reference response',
                                     tofile='Actual response'):

        if line.startswith('+') and not line.startswith('+++'):
            sys.stdout.write(GREEN)
        elif line.startswith('-') and not line.startswith('---'):
            sys.stdout.write(RED)
        elif line.startswith('@@'):
            sys.stdout.write(CYAN)

        sys.stdout.write(line)
        sys.stdout.write(RESET)

    sys.stdout.flush()


def parse_args():
    """Handle flag parsing."""
    parser = argparse.ArgumentParser(
        description='Proxy and compare MPD protocol interactions.')
    parser.add_argument('--listen', default=':6600', type=parse_address,
                        help='address:port to listen on.')
    parser.add_argument('--reference', default=':6601', type=parse_address,
                        help='address:port for the reference backend.')
    parser.add_argument('--actual', default=':6602', type=parse_address,
                        help='address:port for the actual backend.')

    return parser.parse_args()


def parse_address(address):
    """Convert host:port or port to address to pass to connect."""
    if ':' not in address:
        return ('', int(address))
    host, port = address.rsplit(':', 1)
    return (host, int(port))


if __name__ == '__main__':
    args = parse_args()

    def handle(client, address):
        """Wrapper that adds reference and actual backends to proxy calls."""
        return proxy(client, address, args.reference, args.actual)

    try:
        server.StreamServer(args.listen, handle).serve_forever()
    except (KeyboardInterrupt, SystemExit):
        pass

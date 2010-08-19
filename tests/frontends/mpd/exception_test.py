import unittest

from mopidy.frontends.mpd.exceptions import (MpdAckError, MpdUnknownCommand,
    MpdNotImplemented)

class MpdExceptionsTest(unittest.TestCase):
    def test_key_error_wrapped_in_mpd_ack_error(self):
        try:
            try:
                raise KeyError(u'Track X not found')
            except KeyError as e:
                raise MpdAckError(e[0])
        except MpdAckError as e:
            self.assertEqual(e.message, u'Track X not found')

    def test_mpd_not_implemented_is_a_mpd_ack_error(self):
        try:
            raise MpdNotImplemented
        except MpdAckError as e:
            self.assertEqual(e.message, u'Not implemented')

    def test_get_mpd_ack_with_default_values(self):
        e = MpdAckError('A description')
        self.assertEqual(e.get_mpd_ack(), u'ACK [0@0] {} A description')

    def test_get_mpd_ack_with_values(self):
        try:
            raise MpdAckError('A description', error_code=6, index=7,
                command='foo')
        except MpdAckError as e:
            self.assertEqual(e.get_mpd_ack(), u'ACK [6@7] {foo} A description')

    def test_mpd_unknown_command(self):
        try:
            raise MpdUnknownCommand(command=u'play')
        except MpdAckError as e:
            self.assertEqual(e.get_mpd_ack(),
                u'ACK [5@0] {} unknown command "play"')

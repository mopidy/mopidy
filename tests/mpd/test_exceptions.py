from __future__ import absolute_import, unicode_literals

import unittest

from mopidy.mpd.exceptions import (
    MpdAckError, MpdNoCommand, MpdNoExistError, MpdNotImplemented,
    MpdPermissionError, MpdSystemError, MpdUnknownCommand)


class MpdExceptionsTest(unittest.TestCase):

    def test_mpd_not_implemented_is_a_mpd_ack_error(self):
        try:
            raise MpdNotImplemented
        except MpdAckError as e:
            self.assertEqual(e.message, 'Not implemented')

    def test_get_mpd_ack_with_default_values(self):
        e = MpdAckError('A description')
        self.assertEqual(e.get_mpd_ack(), 'ACK [0@0] {None} A description')

    def test_get_mpd_ack_with_values(self):
        try:
            raise MpdAckError('A description', index=7, command='foo')
        except MpdAckError as e:
            self.assertEqual(e.get_mpd_ack(), 'ACK [0@7] {foo} A description')

    def test_mpd_unknown_command(self):
        try:
            raise MpdUnknownCommand(command='play')
        except MpdAckError as e:
            self.assertEqual(
                e.get_mpd_ack(), 'ACK [5@0] {} unknown command "play"')

    def test_mpd_no_command(self):
        try:
            raise MpdNoCommand
        except MpdAckError as e:
            self.assertEqual(
                e.get_mpd_ack(), 'ACK [5@0] {} No command given')

    def test_mpd_system_error(self):
        try:
            raise MpdSystemError('foo')
        except MpdSystemError as e:
            self.assertEqual(
                e.get_mpd_ack(), 'ACK [52@0] {None} foo')

    def test_mpd_permission_error(self):
        try:
            raise MpdPermissionError(command='foo')
        except MpdPermissionError as e:
            self.assertEqual(
                e.get_mpd_ack(),
                'ACK [4@0] {foo} you don\'t have permission for "foo"')

    def test_mpd_noexist_error(self):
        try:
            raise MpdNoExistError(command='foo')
        except MpdNoExistError as e:
            self.assertEqual(
                e.get_mpd_ack(),
                'ACK [50@0] {foo} ')

from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class CommandListsTest(protocol.BaseTestCase):

    def test_command_list_begin(self):
        response = self.send_request('command_list_begin')
        self.assertEqual([], response)

    def test_command_list_end(self):
        self.send_request('command_list_begin')
        self.send_request('command_list_end')
        self.assertInResponse('OK')

    def test_command_list_end_without_start_first_is_an_unknown_command(self):
        self.send_request('command_list_end')
        self.assertEqualResponse(
            'ACK [5@0] {} unknown command "command_list_end"')

    def test_command_list_with_ping(self):
        self.send_request('command_list_begin')
        self.assertTrue(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

        self.send_request('ping')
        self.assertIn('ping', self.dispatcher.command_list)

        self.send_request('command_list_end')
        self.assertInResponse('OK')
        self.assertFalse(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

    def test_command_list_with_error_returns_ack_with_correct_index(self):
        self.send_request('command_list_begin')
        self.send_request('play')  # Known command
        self.send_request('paly')  # Unknown command
        self.send_request('command_list_end')
        self.assertEqualResponse('ACK [5@1] {} unknown command "paly"')

    def test_command_list_ok_begin(self):
        response = self.send_request('command_list_ok_begin')
        self.assertEqual([], response)

    def test_command_list_ok_with_ping(self):
        self.send_request('command_list_ok_begin')
        self.assertTrue(self.dispatcher.command_list_receiving)
        self.assertTrue(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

        self.send_request('ping')
        self.assertIn('ping', self.dispatcher.command_list)

        self.send_request('command_list_end')
        self.assertInResponse('list_OK')
        self.assertInResponse('OK')
        self.assertFalse(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

    # FIXME this should also include the special handling of idle within a
    # command list. That is that once a idle/noidle command is found inside a
    # commad list, the rest of the list seems to be ignored.

from tests.frontends.mpd import protocol


class CommandListsTest(protocol.BaseTestCase):
    def test_command_list_begin(self):
        response = self.sendRequest(u'command_list_begin')
        self.assertEquals([], response)

    def test_command_list_end(self):
        self.sendRequest(u'command_list_begin')
        self.sendRequest(u'command_list_end')
        self.assertInResponse(u'OK')

    def test_command_list_end_without_start_first_is_an_unknown_command(self):
        self.sendRequest(u'command_list_end')
        self.assertEqualResponse(
            u'ACK [5@0] {} unknown command "command_list_end"')

    def test_command_list_with_ping(self):
        self.sendRequest(u'command_list_begin')
        self.assertTrue(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

        self.sendRequest(u'ping')
        self.assertIn(u'ping', self.dispatcher.command_list)

        self.sendRequest(u'command_list_end')
        self.assertInResponse(u'OK')
        self.assertFalse(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

    def test_command_list_with_error_returns_ack_with_correct_index(self):
        self.sendRequest(u'command_list_begin')
        self.sendRequest(u'play')  # Known command
        self.sendRequest(u'paly')  # Unknown command
        self.sendRequest(u'command_list_end')
        self.assertEqualResponse(u'ACK [5@1] {} unknown command "paly"')

    def test_command_list_ok_begin(self):
        response = self.sendRequest(u'command_list_ok_begin')
        self.assertEquals([], response)

    def test_command_list_ok_with_ping(self):
        self.sendRequest(u'command_list_ok_begin')
        self.assertTrue(self.dispatcher.command_list_receiving)
        self.assertTrue(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

        self.sendRequest(u'ping')
        self.assertIn(u'ping', self.dispatcher.command_list)

        self.sendRequest(u'command_list_end')
        self.assertInResponse(u'list_OK')
        self.assertInResponse(u'OK')
        self.assertFalse(self.dispatcher.command_list_receiving)
        self.assertFalse(self.dispatcher.command_list_ok)
        self.assertEqual([], self.dispatcher.command_list)

    # FIXME this should also include the special handling of idle within a
    # command list. That is that once a idle/noidle command is found inside a
    # commad list, the rest of the list seems to be ignored.

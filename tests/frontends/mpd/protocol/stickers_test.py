from __future__ import unicode_literals

from tests.frontends.mpd import protocol


class StickersHandlerTest(protocol.BaseTestCase):
    def test_sticker_get(self):
        self.sendRequest(
            'sticker get "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sticker_set(self):
        self.sendRequest(
            'sticker set "song" "file:///dev/urandom" "a_name" "a_value"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sticker_delete_with_name(self):
        self.sendRequest(
            'sticker delete "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sticker_delete_without_name(self):
        self.sendRequest(
            'sticker delete "song" "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sticker_list(self):
        self.sendRequest(
            'sticker list "song" "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sticker_find(self):
        self.sendRequest(
            'sticker find "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

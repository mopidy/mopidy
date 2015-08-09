from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class StickersHandlerTest(protocol.BaseTestCase):

    def test_sticker_get(self):
        self.send_request(
            'sticker get "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

    def test_sticker_set(self):
        self.send_request(
            'sticker set "song" "file:///dev/urandom" "a_name" "a_value"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

    def test_sticker_delete_with_name(self):
        self.send_request(
            'sticker delete "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

    def test_sticker_delete_without_name(self):
        self.send_request(
            'sticker delete "song" "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

    def test_sticker_list(self):
        self.send_request(
            'sticker list "song" "file:///dev/urandom"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

    def test_sticker_find(self):
        self.send_request(
            'sticker find "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse('ACK [0@0] {sticker} Not implemented')

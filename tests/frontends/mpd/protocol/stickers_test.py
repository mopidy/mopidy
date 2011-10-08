from tests.frontends.mpd import protocol


class StickersHandlerTest(protocol.BaseTestCase):
    def test_sticker_get(self):
        self.sendRequest(
            u'sticker get "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_sticker_set(self):
        self.sendRequest(
            u'sticker set "song" "file:///dev/urandom" "a_name" "a_value"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_sticker_delete_with_name(self):
        self.sendRequest(
            u'sticker delete "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_sticker_delete_without_name(self):
        self.sendRequest(
            u'sticker delete "song" "file:///dev/urandom"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_sticker_list(self):
        self.sendRequest(
            u'sticker list "song" "file:///dev/urandom"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

    def test_sticker_find(self):
        self.sendRequest(
            u'sticker find "song" "file:///dev/urandom" "a_name"')
        self.assertEqualResponse(u'ACK [0@0] {} Not implemented')

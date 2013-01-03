from __future__ import unicode_literals

from tests.frontends.mpd import protocol


class ChannelsHandlerTest(protocol.BaseTestCase):
    def test_subscribe(self):
        self.sendRequest('subscribe "topic"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_unsubscribe(self):
        self.sendRequest('unsubscribe "topic"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_channels(self):
        self.sendRequest('channels')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_readmessages(self):
        self.sendRequest('readmessages')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

    def test_sendmessage(self):
        self.sendRequest('sendmessage "topic" "a message"')
        self.assertEqualResponse('ACK [0@0] {} Not implemented')

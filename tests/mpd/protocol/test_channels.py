from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class ChannelsHandlerTest(protocol.BaseTestCase):

    def test_subscribe(self):
        self.send_request('subscribe "topic"')
        self.assertEqualResponse('ACK [0@0] {subscribe} Not implemented')

    def test_unsubscribe(self):
        self.send_request('unsubscribe "topic"')
        self.assertEqualResponse('ACK [0@0] {unsubscribe} Not implemented')

    def test_channels(self):
        self.send_request('channels')
        self.assertEqualResponse('ACK [0@0] {channels} Not implemented')

    def test_readmessages(self):
        self.send_request('readmessages')
        self.assertEqualResponse('ACK [0@0] {readmessages} Not implemented')

    def test_sendmessage(self):
        self.send_request('sendmessage "topic" "a message"')
        self.assertEqualResponse('ACK [0@0] {sendmessage} Not implemented')

from __future__ import absolute_import, unicode_literals

from tests.mpd import protocol


class MountTest(protocol.BaseTestCase):

    def test_mount(self):
        self.send_request('mount my_disk /dev/sda')
        self.assertEqualResponse('ACK [0@0] {mount} Not implemented')

    def test_unmount(self):
        self.send_request('unmount my_disk')
        self.assertEqualResponse('ACK [0@0] {unmount} Not implemented')

    def test_listmounts(self):
        self.send_request('listmounts')
        self.assertEqualResponse('ACK [0@0] {listmounts} Not implemented')

    def test_listneighbors(self):
        self.send_request('listneighbors')
        self.assertEqualResponse('ACK [0@0] {listneighbors} Not implemented')

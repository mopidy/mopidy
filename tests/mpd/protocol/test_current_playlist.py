from mopidy.internal import deprecation
from mopidy.models import Ref, Track

from tests.mpd import protocol


class AddCommandsTest(protocol.BaseTestCase):
    def setUp(self):  # noqa: N802
        super().setUp()

        self.tracks = [
            Track(uri="dummy:/a", name="a"),
            Track(uri="dummy:/foo/b", name="b"),
            Track(uri="dummy:/foo/ǂ", name="ǂ"),
        ]

        self.refs = {
            "/a": Ref.track(uri="dummy:/a", name="a"),
            "/foo": Ref.directory(uri="dummy:/foo", name="foo"),
            "/foo/b": Ref.track(uri="dummy:/foo/b", name="b"),
            "/foo/ǂ": Ref.track(uri="dummy:/foo/ǂ", name="ǂ"),
        }

        self.backend.library.dummy_library = self.tracks

    def test_add(self):
        for track in [self.tracks[0], self.tracks[0], self.tracks[1]]:
            self.send_request(f'add "{track.uri}"')

        assert len(self.core.tracklist.get_tracks().get()) == 3
        assert self.core.tracklist.get_tracks().get()[2] == self.tracks[1]
        self.assertEqualResponse("OK")

    def test_add_unicode(self):
        for track in [self.tracks[0], self.tracks[1], self.tracks[2]]:
            self.send_request(f'add "{track.uri}"')

        assert len(self.core.tracklist.get_tracks().get()) == 3
        assert self.core.tracklist.get_tracks().get()[2] == self.tracks[2]
        self.assertEqualResponse("OK")

    def test_add_with_uri_not_found_in_library_should_ack(self):
        self.send_request('add "dummy://foo"')
        self.assertEqualResponse("ACK [50@0] {add} directory or file not found")

    def test_add_with_empty_uri_should_not_add_anything_and_ok(self):
        self.backend.library.dummy_browse_result = {
            "dummy:/": [self.refs["/a"]]
        }

        self.send_request('add ""')
        assert len(self.core.tracklist.get_tracks().get()) == 0
        self.assertInResponse("OK")

    def test_add_with_library_should_recurse(self):
        self.backend.library.dummy_browse_result = {
            "dummy:/": [self.refs["/a"], self.refs["/foo"]],
            "dummy:/foo": [self.refs["/foo/b"], self.refs["/foo/ǂ"]],
        }

        self.send_request('add "/dummy"')
        assert self.core.tracklist.get_tracks().get() == self.tracks
        self.assertInResponse("OK")

    def test_add_root_should_not_add_anything_and_ok(self):
        self.backend.library.dummy_browse_result = {
            "dummy:/": [self.refs["/a"]]
        }

        self.send_request('add "/"')
        assert len(self.core.tracklist.get_tracks().get()) == 0
        self.assertInResponse("OK")

    def test_addid_without_songpos(self):
        for track in [self.tracks[0], self.tracks[0], self.tracks[1]]:
            self.send_request(f'addid "{track.uri}"')
        tl_tracks = self.core.tracklist.get_tl_tracks().get()

        assert len(tl_tracks) == 3
        assert tl_tracks[2].track == self.tracks[1]
        self.assertInResponse(f"Id: {tl_tracks[2].tlid:d}")
        self.assertInResponse("OK")

    def test_addid_with_songpos(self):
        for track in [self.tracks[0], self.tracks[0]]:
            self.send_request(f'add "{track.uri}"')
        self.send_request(f'addid "{self.tracks[1].uri}" "1"')
        tl_tracks = self.core.tracklist.get_tl_tracks().get()

        assert len(tl_tracks) == 3
        assert tl_tracks[1].track == self.tracks[1]
        self.assertInResponse(f"Id: {tl_tracks[1].tlid:d}")
        self.assertInResponse("OK")

    def test_addid_with_songpos_out_of_bounds_should_ack(self):
        self.send_request(f'addid "{self.tracks[0].uri}" "3"')
        self.assertEqualResponse("ACK [2@0] {addid} Bad song index")

    def test_addid_with_empty_uri_acks(self):
        self.send_request('addid ""')
        self.assertEqualResponse("ACK [50@0] {addid} No such song")

    def test_addid_with_uri_not_found_in_library_should_ack(self):
        self.send_request('addid "dummy://foo"')
        self.assertEqualResponse("ACK [50@0] {addid} No such song")


class BasePopulatedTracklistTestCase(protocol.BaseTestCase):
    def setUp(self):  # noqa: N802
        super().setUp()
        tracks = [Track(uri=f"dummy:/{x}", name=x) for x in "abcdeǂ"]
        self.backend.library.dummy_library = tracks
        self.core.tracklist.add(uris=[t.uri for t in tracks])


class DeleteCommandsTest(BasePopulatedTracklistTestCase):
    def test_clear(self):
        self.send_request("clear")
        assert len(self.core.tracklist.get_tracks().get()) == 0
        assert self.core.playback.get_current_track().get() is None
        self.assertInResponse("OK")

    def test_delete_songpos(self):
        tl_tracks = self.core.tracklist.get_tl_tracks().get()
        self.send_request(f'delete "{tl_tracks[1].tlid}"')
        assert len(self.core.tracklist.get_tracks().get()) == 5
        self.assertInResponse("OK")

    def test_delete_songpos_out_of_bounds(self):
        self.send_request('delete "8"')
        assert len(self.core.tracklist.get_tracks().get()) == 6
        self.assertEqualResponse("ACK [2@0] {delete} Bad song index")

    def test_delete_open_range(self):
        self.send_request('delete "1:"')
        assert len(self.core.tracklist.get_tracks().get()) == 1
        self.assertInResponse("OK")

    # TODO: check how this should work.
    # def test_delete_open_upper_range(self):
    #     self.send_request('delete ":8"')
    #     self.assertEqual(len(self.core.tracklist.get_tracks().get()), 0)
    #     self.assertInResponse('OK')

    def test_delete_closed_range(self):
        self.send_request('delete "1:3"')
        assert len(self.core.tracklist.get_tracks().get()) == 4
        self.assertInResponse("OK")

    def test_delete_entire_range_out_of_bounds(self):
        self.send_request('delete "8:9"')
        assert len(self.core.tracklist.get_tracks().get()) == 6
        self.assertEqualResponse("ACK [2@0] {delete} Bad song index")

    def test_delete_upper_range_out_of_bounds(self):
        self.send_request('delete "5:9"')
        assert len(self.core.tracklist.get_tracks().get()) == 5
        self.assertEqualResponse("OK")

    def test_deleteid(self):
        self.send_request('deleteid "1"')
        assert len(self.core.tracklist.get_tracks().get()) == 5
        self.assertInResponse("OK")

    def test_deleteid_does_not_exist(self):
        self.send_request('deleteid "12345"')
        assert len(self.core.tracklist.get_tracks().get()) == 6
        self.assertEqualResponse("ACK [50@0] {deleteid} No such song")


class MoveCommandsTest(BasePopulatedTracklistTestCase):
    def test_move_songpos(self):
        self.send_request('move "1" "0"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["b", "a", "c", "d", "e", "ǂ"]
        self.assertInResponse("OK")

    def test_move_open_range(self):
        self.send_request('move "2:" "0"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["c", "d", "e", "ǂ", "a", "b"]
        self.assertInResponse("OK")

    def test_move_closed_range(self):
        self.send_request('move "1:3" "0"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["b", "c", "a", "d", "e", "ǂ"]
        self.assertInResponse("OK")

    def test_moveid(self):
        self.send_request('moveid "5" "2"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["a", "b", "e", "c", "d", "ǂ"]
        self.assertInResponse("OK")

    def test_moveid_with_tlid_not_found_in_tracklist_should_ack(self):
        self.send_request('moveid "10" "0"')
        self.assertEqualResponse("ACK [50@0] {moveid} No such song")


class PlaylistFindCommandTest(protocol.BaseTestCase):
    def test_playlistfind(self):
        self.send_request('playlistfind "tag" "needle"')
        self.assertEqualResponse("ACK [0@0] {playlistfind} Not implemented")

    def test_playlistfind_by_filename_not_in_tracklist(self):
        self.send_request('playlistfind "filename" "file:///dev/null"')
        self.assertEqualResponse("OK")

    def test_playlistfind_by_filename_without_quotes(self):
        self.send_request('playlistfind filename "file:///dev/null"')
        self.assertEqualResponse("OK")

    def test_playlistfind_by_filename_in_tracklist(self):
        track = Track(uri="dummy:///exists")
        self.backend.library.dummy_library = [track]
        self.core.tracklist.add(uris=[track.uri])

        self.send_request('playlistfind filename "dummy:///exists"')
        self.assertInResponse("file: dummy:///exists")
        self.assertInResponse("Id: 1")
        self.assertInResponse("Pos: 0")
        self.assertInResponse("OK")


class PlaylistIdCommandTest(BasePopulatedTracklistTestCase):
    def test_playlistid_without_songid(self):
        self.send_request("playlistid")
        self.assertInResponse("Title: a")
        self.assertInResponse("Title: b")
        self.assertInResponse("OK")

    def test_playlistid_with_songid(self):
        self.send_request('playlistid "2"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Id: 1")
        self.assertInResponse("Title: b")
        self.assertInResponse("Id: 2")
        self.assertInResponse("OK")

    def test_playlistid_with_not_existing_songid_fails(self):
        self.send_request('playlistid "25"')
        self.assertEqualResponse("ACK [50@0] {playlistid} No such song")


class PlaylistInfoCommandTest(BasePopulatedTracklistTestCase):
    def test_playlist_returns_same_as_playlistinfo(self):
        with deprecation.ignore("mpd.protocol.current_playlist.playlist"):
            playlist_response = self.send_request("playlist")

        playlistinfo_response = self.send_request("playlistinfo")
        assert playlist_response == playlistinfo_response

    def test_playlistinfo_without_songpos_or_range(self):
        self.send_request("playlistinfo")
        self.assertInResponse("Title: a")
        self.assertInResponse("Pos: 0")
        self.assertInResponse("Title: b")
        self.assertInResponse("Pos: 1")
        self.assertInResponse("Title: c")
        self.assertInResponse("Pos: 2")
        self.assertInResponse("Title: d")
        self.assertInResponse("Pos: 3")
        self.assertInResponse("Title: e")
        self.assertInResponse("Pos: 4")
        self.assertInResponse("Title: ǂ")
        self.assertInResponse("Pos: 5")
        self.assertInResponse("OK")

    def test_playlistinfo_with_songpos(self):
        # Make the track's CPID not match the playlist position
        self.core.tracklist.tlid = 17

        self.send_request('playlistinfo "4"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Pos: 0")
        self.assertNotInResponse("Title: b")
        self.assertNotInResponse("Pos: 1")
        self.assertNotInResponse("Title: c")
        self.assertNotInResponse("Pos: 2")
        self.assertNotInResponse("Title: d")
        self.assertNotInResponse("Pos: 3")
        self.assertInResponse("Title: e")
        self.assertInResponse("Pos: 4")
        self.assertNotInResponse("Title: ǂ")
        self.assertNotInResponse("Pos: 5")
        self.assertInResponse("OK")

    def test_playlistinfo_with_negative_songpos_same_as_playlistinfo(self):
        response1 = self.send_request('playlistinfo "-1"')
        response2 = self.send_request("playlistinfo")
        assert response1 == response2

    def test_playlistinfo_with_open_range(self):
        self.send_request('playlistinfo "2:"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Pos: 0")
        self.assertNotInResponse("Title: b")
        self.assertNotInResponse("Pos: 1")
        self.assertInResponse("Title: c")
        self.assertInResponse("Pos: 2")
        self.assertInResponse("Title: d")
        self.assertInResponse("Pos: 3")
        self.assertInResponse("Title: e")
        self.assertInResponse("Pos: 4")
        self.assertInResponse("Title: ǂ")
        self.assertInResponse("Pos: 5")
        self.assertInResponse("OK")

    def test_playlistinfo_with_closed_range(self):
        self.send_request('playlistinfo "2:4"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Title: b")
        self.assertInResponse("Title: c")
        self.assertInResponse("Title: d")
        self.assertNotInResponse("Title: e")
        self.assertNotInResponse("Title: ǂ")
        self.assertInResponse("OK")

    def test_playlistinfo_with_too_high_start_of_range_returns_arg_error(self):
        self.send_request('playlistinfo "10:20"')
        self.assertEqualResponse("ACK [2@0] {playlistinfo} Bad song index")

    def test_playlistinfo_with_too_high_end_of_range_returns_ok(self):
        self.send_request('playlistinfo "0:20"')
        self.assertInResponse("OK")

    def test_playlistinfo_with_zero_returns_ok(self):
        self.send_request('playlistinfo "0"')
        self.assertInResponse("OK")


class PlaylistSearchCommandTest(protocol.BaseTestCase):
    def test_playlistsearch(self):
        self.send_request('playlistsearch "any" "needle"')
        self.assertEqualResponse("ACK [0@0] {playlistsearch} Not implemented")

    def test_playlistsearch_without_quotes(self):
        self.send_request('playlistsearch any "needle"')
        self.assertEqualResponse("ACK [0@0] {playlistsearch} Not implemented")


class PlChangeCommandTest(BasePopulatedTracklistTestCase):
    def test_plchanges_with_lower_version_returns_changes(self):
        self.send_request('plchanges "0"')
        self.assertInResponse("Title: a")
        self.assertInResponse("Title: b")
        self.assertInResponse("Title: c")
        self.assertInResponse("OK")

    def test_plchanges_with_equal_version_returns_nothing(self):
        assert self.core.tracklist.get_version().get() == 1
        self.send_request('plchanges "1"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Title: b")
        self.assertNotInResponse("Title: c")
        self.assertInResponse("OK")

    def test_plchanges_with_greater_version_returns_nothing(self):
        assert self.core.tracklist.get_version().get() == 1
        self.send_request('plchanges "2"')
        self.assertNotInResponse("Title: a")
        self.assertNotInResponse("Title: b")
        self.assertNotInResponse("Title: c")
        self.assertInResponse("OK")

    def test_plchanges_with_minus_one_returns_entire_playlist(self):
        self.send_request('plchanges "-1"')
        self.assertInResponse("Title: a")
        self.assertInResponse("Title: b")
        self.assertInResponse("Title: c")
        self.assertInResponse("OK")

    def test_plchanges_without_quotes_works(self):
        self.send_request("plchanges 0")
        self.assertInResponse("Title: a")
        self.assertInResponse("Title: b")
        self.assertInResponse("Title: c")
        self.assertInResponse("OK")

    def test_plchangesposid(self):
        self.send_request('plchangesposid "0"')
        tl_tracks = self.core.tracklist.get_tl_tracks().get()
        self.assertInResponse("cpos: 0")
        self.assertInResponse(f"Id: {tl_tracks[0].tlid:d}")
        self.assertInResponse("cpos: 2")
        self.assertInResponse(f"Id: {tl_tracks[1].tlid:d}")
        self.assertInResponse("cpos: 2")
        self.assertInResponse(f"Id: {tl_tracks[2].tlid:d}")
        self.assertInResponse("OK")


class PrioCommandTest(protocol.BaseTestCase):
    def test_prio(self):
        self.send_request("prio 255 0:10")
        self.assertEqualResponse("ACK [0@0] {prio} Not implemented")

    def test_prioid(self):
        self.send_request("prioid 255 17 23")
        self.assertEqualResponse("ACK [0@0] {prioid} Not implemented")


class RangeIdCommandTest(protocol.BaseTestCase):
    def test_rangeid(self):
        self.send_request("rangeid 17 0:30")
        self.assertEqualResponse("ACK [0@0] {rangeid} Not implemented")


# TODO: we only seem to be testing that don't touch the non shuffled region :/
class ShuffleCommandTest(BasePopulatedTracklistTestCase):
    def test_shuffle_without_range(self):
        version = self.core.tracklist.get_version().get()

        self.send_request("shuffle")
        assert version < self.core.tracklist.get_version().get()
        self.assertInResponse("OK")

    def test_shuffle_with_open_range(self):
        version = self.core.tracklist.get_version().get()

        self.send_request('shuffle "4:"')
        assert version < self.core.tracklist.get_version().get()

        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result[:4] == ["a", "b", "c", "d"]
        self.assertInResponse("OK")

    def test_shuffle_with_closed_range(self):
        version = self.core.tracklist.get_version().get()

        self.send_request('shuffle "1:3"')
        assert version < self.core.tracklist.get_version().get()

        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result[:1] == ["a"]
        assert result[3:] == ["d", "e", "ǂ"]
        self.assertInResponse("OK")


class SwapCommandTest(BasePopulatedTracklistTestCase):
    def test_swap(self):
        self.send_request('swap "1" "4"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["a", "e", "c", "d", "b", "ǂ"]
        self.assertInResponse("OK")

    def test_swap_highest_position_first(self):
        self.send_request('swap "4" "1"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["a", "e", "c", "d", "b", "ǂ"]
        self.assertInResponse("OK")

    def test_swapid(self):
        self.send_request('swapid "2" "5"')
        result = [t.name for t in self.core.tracklist.get_tracks().get()]
        assert result == ["a", "e", "c", "d", "b", "ǂ"]
        self.assertInResponse("OK")

    def test_swapid_with_first_id_unknown_should_ack(self):
        self.send_request('swapid "1" "8"')
        self.assertEqualResponse("ACK [50@0] {swapid} No such song")

    def test_swapid_with_second_id_unknown_should_ack(self):
        self.send_request('swapid "8" "1"')
        self.assertEqualResponse("ACK [50@0] {swapid} No such song")


class TagCommandTest(protocol.BaseTestCase):
    def test_addtagid(self):
        self.send_request("addtagid 17 artist Abba")
        self.assertEqualResponse("ACK [0@0] {addtagid} Not implemented")

    def test_cleartagid(self):
        self.send_request("cleartagid 17 artist")
        self.assertEqualResponse("ACK [0@0] {cleartagid} Not implemented")

import pathlib
import platform
import shutil
import tempfile
import unittest

import pykka

from mopidy import core
from mopidy.m3u.backend import M3UBackend
from mopidy.models import Playlist, Track

from tests import dummy_audio, path_to_data_dir
from tests.m3u import generate_song


class M3UPlaylistsProviderTest(unittest.TestCase):
    backend_class = M3UBackend
    config = {
        "m3u": {
            "enabled": True,
            "base_dir": None,
            "default_encoding": "latin-1",
            "default_extension": ".m3u",
            "playlists_dir": path_to_data_dir(""),
        }
    }

    def setUp(self):  # noqa: N802
        self.config["m3u"]["playlists_dir"] = pathlib.Path(tempfile.mkdtemp())
        self.playlists_dir = self.config["m3u"]["playlists_dir"]
        self.base_dir = self.config["m3u"]["base_dir"] or self.playlists_dir

        audio = dummy_audio.create_proxy()
        backend = M3UBackend.start(config=self.config, audio=audio).proxy()
        self.core = core.Core(backends=[backend])

    def tearDown(self):  # noqa: N802
        pykka.ActorRegistry.stop_all()

        if self.playlists_dir.exists():
            shutil.rmtree(str(self.playlists_dir))

    def test_created_playlist_is_persisted(self):
        uri = "m3u:test.m3u"
        path = self.playlists_dir / "test.m3u"
        assert not path.exists()

        playlist = self.core.playlists.create("test")
        assert "test" == playlist.name
        assert uri == playlist.uri
        assert path.exists()

    def test_create_sanitizes_playlist_name(self):
        playlist = self.core.playlists.create("  ../../test FOO baR ")
        assert "..|..|test FOO baR" == playlist.name
        path = self.playlists_dir / "..|..|test FOO baR.m3u"
        assert self.playlists_dir == path.parent
        assert path.exists()

    def test_saved_playlist_is_persisted(self):
        uri1 = "m3u:test1.m3u"
        uri2 = "m3u:test2.m3u"

        path1 = self.playlists_dir / "test1.m3u"
        path2 = self.playlists_dir / "test2.m3u"

        playlist = self.core.playlists.create("test1")
        assert "test1" == playlist.name
        assert uri1 == playlist.uri
        assert path1.exists()
        assert not path2.exists()

        playlist = self.core.playlists.save(playlist.replace(name="test2"))
        assert "test2" == playlist.name
        assert uri2 == playlist.uri
        assert not path1.exists()
        assert path2.exists()

    def test_deleted_playlist_is_removed(self):
        uri = "m3u:test.m3u"
        path = self.playlists_dir / "test.m3u"

        assert not path.exists()

        playlist = self.core.playlists.create("test")
        assert "test" == playlist.name
        assert uri == playlist.uri
        assert path.exists()

        success = self.core.playlists.delete(playlist.uri)
        assert success
        assert not path.exists()

    def test_delete_on_path_outside_playlist_dir_returns_none(self):
        success = self.core.playlists.delete("m3u:///etc/passwd")

        assert not success

    def test_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1))
        playlist = self.core.playlists.create("test")
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = self.playlists_dir / "test.m3u"

        contents = path.read_text()

        assert track.uri == contents.strip()

    def test_extended_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1), name="Test", length=60000)
        playlist = self.core.playlists.create("test")
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = self.playlists_dir / "test.m3u"

        m3u = path.read_text().splitlines()

        assert ["#EXTM3U", "#EXTINF:-1,Test", track.uri] == m3u

    def test_latin1_playlist_contents_is_written_to_disk(self):
        track = Track(uri=generate_song(1), name="Test\x9f", length=60000)
        playlist = self.core.playlists.create("test")
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = self.playlists_dir / "test.m3u"

        m3u = path.read_bytes().splitlines()

        track_uri = track.uri
        if not isinstance(track_uri, bytes):
            track_uri = track.uri.encode()
        assert [b"#EXTM3U", b"#EXTINF:-1,Test\x9f", track_uri] == m3u

    def test_utf8_playlist_contents_is_replaced_and_written_to_disk(self):
        track = Track(uri=generate_song(1), name="Test\u07b4", length=60000)
        playlist = self.core.playlists.create("test")
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))
        path = self.playlists_dir / "test.m3u"

        m3u = path.read_bytes().splitlines()

        track_uri = track.uri
        if not isinstance(track_uri, bytes):
            track_uri = track.uri.encode()
        assert [b"#EXTM3U", b"#EXTINF:-1,Test?", track_uri] == m3u

    def test_playlists_are_loaded_at_startup(self):
        track = Track(uri="dummy:track:path2")
        playlist = self.core.playlists.create("test")
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        assert len(self.core.playlists.as_list()) == 1
        result = self.core.playlists.lookup(playlist.uri)
        assert playlist.uri == result.uri
        assert playlist.name == result.name
        assert track.uri == result.tracks[0].uri

    @unittest.skipIf(
        platform.system() == "Darwin",
        'macOS 10.13 raises IOError "Illegal byte sequence" on open.',
    )
    def test_load_playlist_with_nonfilesystem_encoding_of_filename(self):
        playlist_name = "øæå.m3u".encode("latin-1")
        playlist_name = playlist_name.decode(errors="surrogateescape")
        path = self.playlists_dir / playlist_name
        path.write_bytes(b"#EXTM3U\n")

        self.core.playlists.refresh()

        assert len(self.core.playlists.as_list()) == 1
        result = self.core.playlists.as_list()
        assert "���" == result[0].name

    @unittest.SkipTest
    def test_playlists_dir_is_created(self):
        pass

    def test_create_returns_playlist_with_name_set(self):
        playlist = self.core.playlists.create("test")
        assert playlist.name == "test"

    def test_create_returns_playlist_with_uri_set(self):
        playlist = self.core.playlists.create("test")
        assert playlist.uri

    def test_create_adds_playlist_to_playlists_collection(self):
        playlist = self.core.playlists.create("test")
        playlists = self.core.playlists.as_list()
        assert playlist.uri in [ref.uri for ref in playlists]

    def test_as_list_empty_to_start_with(self):
        assert len(self.core.playlists.as_list()) == 0

    def test_as_list_ignores_non_playlists(self):
        path = self.playlists_dir / "test.foo"
        path.touch()
        assert path.exists()

        self.core.playlists.refresh()

        assert len(self.core.playlists.as_list()) == 0

    def test_delete_non_existant_playlist(self):
        self.core.playlists.delete("m3u:unknown")

    def test_delete_playlist_removes_it_from_the_collection(self):
        playlist = self.core.playlists.create("test")
        assert playlist == self.core.playlists.lookup(playlist.uri)

        self.core.playlists.delete(playlist.uri)

        assert self.core.playlists.lookup(playlist.uri) is None

    def test_delete_playlist_without_file(self):
        playlist = self.core.playlists.create("test")
        assert playlist == self.core.playlists.lookup(playlist.uri)

        path = self.playlists_dir / "test.m3u"
        assert path.exists()

        path.unlink()
        assert not path.exists()

        self.core.playlists.delete(playlist.uri)
        assert self.core.playlists.lookup(playlist.uri) is None

    def test_lookup_finds_playlist_by_uri(self):
        original_playlist = self.core.playlists.create("test")

        looked_up_playlist = self.core.playlists.lookup(original_playlist.uri)

        assert original_playlist == looked_up_playlist

    def test_lookup_on_path_outside_playlist_dir_returns_none(self):
        result = self.core.playlists.lookup("m3u:///etc/passwd")

        assert result is None

    def test_refresh(self):
        playlist = self.core.playlists.create("test")
        assert playlist == self.core.playlists.lookup(playlist.uri)

        self.core.playlists.refresh()

        assert playlist == self.core.playlists.lookup(playlist.uri)

    def test_save_replaces_existing_playlist_with_updated_playlist(self):
        playlist1 = self.core.playlists.create("test1")
        assert playlist1 == self.core.playlists.lookup(playlist1.uri)

        playlist2 = playlist1.replace(name="test2")
        playlist2 = self.core.playlists.save(playlist2)
        assert self.core.playlists.lookup(playlist1.uri) is None
        assert playlist2 == self.core.playlists.lookup(playlist2.uri)

    def test_create_replaces_existing_playlist_with_updated_playlist(self):
        track = Track(uri=generate_song(1))
        playlist1 = self.core.playlists.create("test")
        playlist1 = self.core.playlists.save(playlist1.replace(tracks=[track]))
        assert playlist1 == self.core.playlists.lookup(playlist1.uri)

        playlist2 = self.core.playlists.create("test")
        assert playlist1.uri == playlist2.uri
        assert playlist1 != self.core.playlists.lookup(playlist1.uri)
        assert playlist2 == self.core.playlists.lookup(playlist1.uri)

    def test_save_playlist_with_new_uri(self):
        uri = "m3u:test.m3u"
        self.core.playlists.save(Playlist(uri=uri))
        path = self.playlists_dir / "test.m3u"
        assert path.exists()

    def test_save_on_path_outside_playlist_dir_returns_none(self):
        result = self.core.playlists.save(Playlist(uri="m3u:///tmp/test.m3u"))
        assert result is None

    def test_playlist_with_unknown_track(self):
        track = Track(uri="file:///dev/null")
        playlist = self.core.playlists.create("test")
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        assert len(self.core.playlists.as_list()) == 1
        result = self.core.playlists.lookup("m3u:test.m3u")
        assert "m3u:test.m3u" == result.uri
        assert playlist.name == result.name
        assert track.uri == result.tracks[0].uri

    def test_playlist_with_absolute_path(self):
        track = Track(uri="/tmp/test.mp3")
        filepath = pathlib.Path("/tmp/test.mp3")
        playlist = self.core.playlists.create("test")
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        assert len(self.core.playlists.as_list()) == 1
        result = self.core.playlists.lookup("m3u:test.m3u")
        assert "m3u:test.m3u" == result.uri
        assert playlist.name == result.name
        assert filepath.as_uri() == result.tracks[0].uri

    def test_playlist_with_relative_path(self):
        track = Track(uri="test.mp3")
        filepath = self.base_dir / "test.mp3"
        playlist = self.core.playlists.create("test")
        playlist = playlist.replace(tracks=[track])
        playlist = self.core.playlists.save(playlist)

        assert len(self.core.playlists.as_list()) == 1
        result = self.core.playlists.lookup("m3u:test.m3u")
        assert "m3u:test.m3u" == result.uri
        assert playlist.name == result.name
        assert filepath.as_uri() == result.tracks[0].uri

    def test_playlist_sort_order(self):
        def check_order(playlists, names):
            assert names == [playlist.name for playlist in playlists]

        self.core.playlists.create("c")
        self.core.playlists.create("a")
        self.core.playlists.create("b")

        check_order(self.core.playlists.as_list(), ["a", "b", "c"])

        self.core.playlists.refresh()

        check_order(self.core.playlists.as_list(), ["a", "b", "c"])

        playlist = self.core.playlists.lookup("m3u:a.m3u")
        playlist = playlist.replace(name="d")
        playlist = self.core.playlists.save(playlist)

        check_order(self.core.playlists.as_list(), ["b", "c", "d"])

        self.core.playlists.delete("m3u:c.m3u")

        check_order(self.core.playlists.as_list(), ["b", "d"])

    def test_get_items_returns_item_refs(self):
        track = Track(uri="dummy:a", name="A", length=60000)
        playlist = self.core.playlists.create("test")
        playlist = self.core.playlists.save(playlist.replace(tracks=[track]))

        item_refs = self.core.playlists.get_items(playlist.uri)

        assert len(item_refs) == 1
        assert item_refs[0].type == "track"
        assert item_refs[0].uri == "dummy:a"
        assert item_refs[0].name == "A"

    def test_get_items_of_unknown_playlist_returns_none(self):
        item_refs = self.core.playlists.get_items("dummy:unknown")

        assert item_refs is None

    def test_get_items_from_file_outside_playlist_dir_returns_none(self):
        item_refs = self.core.playlists.get_items("m3u:///etc/passwd")

        assert item_refs is None


class M3UPlaylistsProviderBaseDirectoryTest(M3UPlaylistsProviderTest):
    def setUp(self):  # noqa: N802
        self.config["m3u"]["base_dir"] = pathlib.Path(tempfile.mkdtemp())
        super().setUp()

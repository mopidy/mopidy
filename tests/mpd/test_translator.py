import unittest

from mopidy.models import Album, Artist, Playlist, TlTrack, Track
from mopidy.mpd import translator

from tests import path_utils


class TrackMpdFormatTest(unittest.TestCase):
    track = Track(
        uri="à uri",
        artists=[Artist(name="an artist")],
        name="a nàme",
        album=Album(
            name="an album",
            num_tracks=13,
            artists=[Artist(name="an other artist")],
            uri="urischeme:àlbum:12345",
        ),
        track_no=7,
        composers=[Artist(name="a composer")],
        performers=[Artist(name="a performer")],
        genre="a genre",
        date="1977-01-01",
        disc_no=1,
        comment="a comment",
        length=137000,
    )

    def setUp(self):  # noqa: N802
        self.media_dir = "/dir/subdir"
        path_utils.mtime.set_fake_time(1234567)

    def tearDown(self):  # noqa: N802
        path_utils.mtime.undo_fake()

    def test_track_to_mpd_format_for_empty_track(self):
        result = translator.track_to_mpd_format(
            Track(uri="a uri", length=137000)
        )
        assert ("file", "a uri") in result
        assert ("Time", 137) in result
        assert ("Artist", "") not in result
        assert ("Title", "") not in result
        assert ("Album", "") not in result
        assert ("Track", 0) not in result
        assert ("Date", "") not in result
        assert len(result) == 2

    def test_track_to_mpd_format_with_position(self):
        result = translator.track_to_mpd_format(Track(), position=1)
        assert ("Pos", 1) not in result

    def test_track_to_mpd_format_with_tlid(self):
        result = translator.track_to_mpd_format(TlTrack(1, Track()))
        assert ("Id", 1) not in result

    def test_track_to_mpd_format_with_position_and_tlid(self):
        result = translator.track_to_mpd_format(
            TlTrack(2, Track(uri="a uri")), position=1
        )
        assert ("Pos", 1) in result
        assert ("Id", 2) in result

    def test_track_to_mpd_format_for_nonempty_track(self):
        result = translator.track_to_mpd_format(
            TlTrack(122, self.track), position=9
        )
        assert ("file", "à uri") in result
        assert ("Time", 137) in result
        assert ("Artist", "an artist") in result
        assert ("Title", "a nàme") in result
        assert ("Album", "an album") in result
        assert ("AlbumArtist", "an other artist") in result
        assert ("Composer", "a composer") in result
        assert ("Performer", "a performer") in result
        assert ("Genre", "a genre") in result
        assert ("Track", "7/13") in result
        assert ("Date", "1977-01-01") in result
        assert ("Disc", 1) in result
        assert ("Pos", 9) in result
        assert ("Id", 122) in result
        assert ("X-AlbumUri", "urischeme:àlbum:12345") in result
        assert ("Comment", "a comment") not in result
        assert len(result) == 15

    def test_track_to_mpd_format_with_last_modified(self):
        track = self.track.replace(last_modified=995303899000)
        result = translator.track_to_mpd_format(track)
        assert ("Last-Modified", "2001-07-16T17:18:19Z") in result

    def test_track_to_mpd_format_with_last_modified_of_zero(self):
        track = self.track.replace(last_modified=0)
        result = translator.track_to_mpd_format(track)
        keys = [k for k, v in result]
        assert "Last-Modified" not in keys

    def test_track_to_mpd_format_musicbrainz_trackid(self):
        track = self.track.replace(musicbrainz_id="foo")
        result = translator.track_to_mpd_format(track)
        assert ("MUSICBRAINZ_TRACKID", "foo") in result

    def test_track_to_mpd_format_musicbrainz_albumid(self):
        album = self.track.album.replace(musicbrainz_id="foo")
        track = self.track.replace(album=album)
        result = translator.track_to_mpd_format(track)
        assert ("MUSICBRAINZ_ALBUMID", "foo") in result

    def test_track_to_mpd_format_musicbrainz_albumartistid(self):
        artist = list(self.track.artists)[0].replace(musicbrainz_id="foo")
        album = self.track.album.replace(artists=[artist])
        track = self.track.replace(album=album)
        result = translator.track_to_mpd_format(track)
        assert ("MUSICBRAINZ_ALBUMARTISTID", "foo") in result

    def test_track_to_mpd_format_musicbrainz_artistid(self):
        artist = list(self.track.artists)[0].replace(musicbrainz_id="foo")
        track = self.track.replace(artists=[artist])
        result = translator.track_to_mpd_format(track)
        assert ("MUSICBRAINZ_ARTISTID", "foo") in result

    def test_concat_multi_values(self):
        artists = [Artist(name="ABBA"), Artist(name="Beatles")]
        translated = translator.concat_multi_values(artists, "name")
        assert translated == "ABBA;Beatles"

    def test_concat_multi_values_artist_with_no_name(self):
        artists = [Artist(name=None)]
        translated = translator.concat_multi_values(artists, "name")
        assert translated == ""

    def test_concat_multi_values_artist_with_no_musicbrainz_id(self):
        artists = [Artist(name="Jah Wobble")]
        translated = translator.concat_multi_values(artists, "musicbrainz_id")
        assert translated == ""

    def test_track_to_mpd_format_with_stream_title(self):
        result = translator.track_to_mpd_format(self.track, stream_title="foo")
        assert ("Name", "a nàme") in result
        assert ("Title", "foo") in result

    def test_track_to_mpd_format_with_empty_stream_title(self):
        result = translator.track_to_mpd_format(self.track, stream_title="")
        assert ("Name", "a nàme") in result
        assert ("Title", "") not in result

    def test_track_to_mpd_format_with_stream_and_no_track_name(self):
        track = self.track.replace(name=None)
        result = translator.track_to_mpd_format(track, stream_title="foo")
        assert ("Name", "") not in result
        assert ("Title", "foo") in result


class PlaylistMpdFormatTest(unittest.TestCase):
    def test_mpd_format(self):
        playlist = Playlist(
            tracks=[
                Track(uri="foo", track_no=1),
                Track(uri="bàr", track_no=2),
                Track(uri="baz", track_no=3),
            ]
        )
        result = translator.playlist_to_mpd_format(playlist)
        assert len(result) == 3

    def test_mpd_format_with_range(self):
        playlist = Playlist(
            tracks=[
                Track(uri="foo", track_no=1),
                Track(uri="bàr", track_no=2),
                Track(uri="baz", track_no=3),
            ]
        )
        result = translator.playlist_to_mpd_format(playlist, 1, 2)
        assert len(result) == 1
        assert dict(result[0])["Track"] == 2

from __future__ import absolute_import, unicode_literals

import datetime
import unittest

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

import pytest

from mopidy.audio import utils
from mopidy.models import Album, Artist, Track


class TestCreateBuffer(object):

    def test_creates_buffer(self):
        buf = utils.create_buffer(b'123', timestamp=0, duration=1000000)

        assert isinstance(buf, Gst.Buffer)
        assert buf.pts == 0
        assert buf.duration == 1000000
        assert buf.get_size() == len(b'123')

    def test_fails_if_data_has_zero_length(self):
        with pytest.raises(ValueError) as excinfo:
            utils.create_buffer(b'', timestamp=0, duration=1000000)

        assert 'Cannot create buffer without data' in str(excinfo.value)


# TODO: keep ids without name?
# TODO: current test is trying to test everything at once with a complete tags
# set, instead we might want to try with a minimal one making testing easier.
class TagsToTrackTest(unittest.TestCase):

    def setUp(self):  # noqa: N802
        self.tags = {
            'album': ['album'],
            'track-number': [1],
            'artist': ['artist'],
            'composer': ['composer'],
            'performer': ['performer'],
            'album-artist': ['albumartist'],
            'title': ['track'],
            'track-count': [2],
            'album-disc-number': [2],
            'album-disc-count': [3],
            'date': [datetime.date(2006, 1, 1,)],
            'container-format': ['ID3 tag'],
            'genre': ['genre'],
            'comment': ['comment'],
            'musicbrainz-trackid': ['trackid'],
            'musicbrainz-albumid': ['albumid'],
            'musicbrainz-artistid': ['artistid'],
            'musicbrainz-sortname': ['sortname'],
            'musicbrainz-albumartistid': ['albumartistid'],
            'bitrate': [1000],
        }

        artist = Artist(name='artist', musicbrainz_id='artistid',
                        sortname='sortname')
        composer = Artist(name='composer')
        performer = Artist(name='performer')
        albumartist = Artist(name='albumartist',
                             musicbrainz_id='albumartistid')

        album = Album(name='album', num_tracks=2, num_discs=3,
                      musicbrainz_id='albumid', artists=[albumartist])

        self.track = Track(name='track', date='2006-01-01',
                           genre='genre', track_no=1, disc_no=2,
                           comment='comment', musicbrainz_id='trackid',
                           album=album, bitrate=1000, artists=[artist],
                           composers=[composer], performers=[performer])

    def check(self, expected):
        actual = utils.convert_tags_to_track(self.tags)
        self.assertEqual(expected, actual)

    def test_track(self):
        self.check(self.track)

    def test_missing_track_no(self):
        del self.tags['track-number']
        self.check(self.track.replace(track_no=None))

    def test_multiple_track_no(self):
        self.tags['track-number'].append(9)
        self.check(self.track)

    def test_missing_track_disc_no(self):
        del self.tags['album-disc-number']
        self.check(self.track.replace(disc_no=None))

    def test_multiple_track_disc_no(self):
        self.tags['album-disc-number'].append(9)
        self.check(self.track)

    def test_missing_track_name(self):
        del self.tags['title']
        self.check(self.track.replace(name=None))

    def test_multiple_track_name(self):
        self.tags['title'] = ['name1', 'name2']
        self.check(self.track.replace(name='name1; name2'))

    def test_missing_track_musicbrainz_id(self):
        del self.tags['musicbrainz-trackid']
        self.check(self.track.replace(musicbrainz_id=None))

    def test_multiple_track_musicbrainz_id(self):
        self.tags['musicbrainz-trackid'].append('id')
        self.check(self.track)

    def test_missing_track_bitrate(self):
        del self.tags['bitrate']
        self.check(self.track.replace(bitrate=None))

    def test_multiple_track_bitrate(self):
        self.tags['bitrate'].append(1234)
        self.check(self.track)

    def test_missing_track_genre(self):
        del self.tags['genre']
        self.check(self.track.replace(genre=None))

    def test_multiple_track_genre(self):
        self.tags['genre'] = ['genre1', 'genre2']
        self.check(self.track.replace(genre='genre1; genre2'))

    def test_missing_track_date(self):
        del self.tags['date']
        self.check(self.track.replace(date=None))

    def test_multiple_track_date(self):
        self.tags['date'].append(datetime.date(2030, 1, 1))
        self.check(self.track)

    def test_missing_track_comment(self):
        del self.tags['comment']
        self.check(self.track.replace(comment=None))

    def test_multiple_track_comment(self):
        self.tags['comment'] = ['comment1', 'comment2']
        self.check(self.track.replace(comment='comment1; comment2'))

    def test_missing_track_artist_name(self):
        del self.tags['artist']
        self.check(self.track.replace(artists=[]))

    def test_multiple_track_artist_name(self):
        self.tags['artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        self.check(self.track.replace(artists=artists))

    def test_missing_track_artist_musicbrainz_id(self):
        del self.tags['musicbrainz-artistid']
        artist = list(self.track.artists)[0].replace(musicbrainz_id=None)
        self.check(self.track.replace(artists=[artist]))

    def test_multiple_track_artist_musicbrainz_id(self):
        self.tags['musicbrainz-artistid'].append('id')
        self.check(self.track)

    def test_missing_track_composer_name(self):
        del self.tags['composer']
        self.check(self.track.replace(composers=[]))

    def test_multiple_track_composer_name(self):
        self.tags['composer'] = ['composer1', 'composer2']
        composers = [Artist(name='composer1'), Artist(name='composer2')]
        self.check(self.track.replace(composers=composers))

    def test_missing_track_performer_name(self):
        del self.tags['performer']
        self.check(self.track.replace(performers=[]))

    def test_multiple_track_performe_name(self):
        self.tags['performer'] = ['performer1', 'performer2']
        performers = [Artist(name='performer1'), Artist(name='performer2')]
        self.check(self.track.replace(performers=performers))

    def test_missing_album_name(self):
        del self.tags['album']
        self.check(self.track.replace(album=None))

    def test_multiple_album_name(self):
        self.tags['album'].append('album2')
        self.check(self.track)

    def test_missing_album_musicbrainz_id(self):
        del self.tags['musicbrainz-albumid']
        album = self.track.album.replace(musicbrainz_id=None,
                                         images=[])
        self.check(self.track.replace(album=album))

    def test_multiple_album_musicbrainz_id(self):
        self.tags['musicbrainz-albumid'].append('id')
        self.check(self.track)

    def test_missing_album_num_tracks(self):
        del self.tags['track-count']
        album = self.track.album.replace(num_tracks=None)
        self.check(self.track.replace(album=album))

    def test_multiple_album_num_tracks(self):
        self.tags['track-count'].append(9)
        self.check(self.track)

    def test_missing_album_num_discs(self):
        del self.tags['album-disc-count']
        album = self.track.album.replace(num_discs=None)
        self.check(self.track.replace(album=album))

    def test_multiple_album_num_discs(self):
        self.tags['album-disc-count'].append(9)
        self.check(self.track)

    def test_missing_album_artist_name(self):
        del self.tags['album-artist']
        album = self.track.album.replace(artists=[])
        self.check(self.track.replace(album=album))

    def test_multiple_album_artist_name(self):
        self.tags['album-artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        album = self.track.album.replace(artists=artists)
        self.check(self.track.replace(album=album))

    def test_missing_album_artist_musicbrainz_id(self):
        del self.tags['musicbrainz-albumartistid']
        albumartist = list(self.track.album.artists)[0]
        albumartist = albumartist.replace(musicbrainz_id=None)
        album = self.track.album.replace(artists=[albumartist])
        self.check(self.track.replace(album=album))

    def test_multiple_album_artist_musicbrainz_id(self):
        self.tags['musicbrainz-albumartistid'].append('id')
        self.check(self.track)

    def test_stream_organization_track_name(self):
        del self.tags['title']
        self.tags['organization'] = ['organization']
        self.check(self.track.replace(name='organization'))

    def test_multiple_organization_track_name(self):
        del self.tags['title']
        self.tags['organization'] = ['organization1', 'organization2']
        self.check(self.track.replace(name='organization1; organization2'))

    # TODO: combine all comment types?
    def test_stream_location_track_comment(self):
        del self.tags['comment']
        self.tags['location'] = ['location']
        self.check(self.track.replace(comment='location'))

    def test_multiple_location_track_comment(self):
        del self.tags['comment']
        self.tags['location'] = ['location1', 'location2']
        self.check(self.track.replace(comment='location1; location2'))

    def test_stream_copyright_track_comment(self):
        del self.tags['comment']
        self.tags['copyright'] = ['copyright']
        self.check(self.track.replace(comment='copyright'))

    def test_multiple_copyright_track_comment(self):
        del self.tags['comment']
        self.tags['copyright'] = ['copyright1', 'copyright2']
        self.check(self.track.replace(comment='copyright1; copyright2'))

    def test_sortname(self):
        self.tags['musicbrainz-sortname'] = ['another_sortname']
        artist = Artist(name='artist', sortname='another_sortname',
                        musicbrainz_id='artistid')
        self.check(self.track.replace(artists=[artist]))

    def test_missing_sortname(self):
        del self.tags['musicbrainz-sortname']
        artist = Artist(name='artist', sortname=None,
                        musicbrainz_id='artistid')
        self.check(self.track.replace(artists=[artist]))

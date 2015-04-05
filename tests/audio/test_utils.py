from __future__ import absolute_import, unicode_literals

import datetime
import unittest

from mopidy.audio import utils
from mopidy.models import Album, Artist, Track


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
            'musicbrainz-albumartistid': ['albumartistid'],
            'bitrate': [1000],
        }

        artist = Artist(name='artist', musicbrainz_id='artistid')
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
        self.check(self.track.copy(track_no=None))

    def test_multiple_track_no(self):
        self.tags['track-number'].append(9)
        self.check(self.track)

    def test_missing_track_disc_no(self):
        del self.tags['album-disc-number']
        self.check(self.track.copy(disc_no=None))

    def test_multiple_track_disc_no(self):
        self.tags['album-disc-number'].append(9)
        self.check(self.track)

    def test_missing_track_name(self):
        del self.tags['title']
        self.check(self.track.copy(name=None))

    def test_multiple_track_name(self):
        self.tags['title'] = ['name1', 'name2']
        self.check(self.track.copy(name='name1; name2'))

    def test_missing_track_musicbrainz_id(self):
        del self.tags['musicbrainz-trackid']
        self.check(self.track.copy(musicbrainz_id=None))

    def test_multiple_track_musicbrainz_id(self):
        self.tags['musicbrainz-trackid'].append('id')
        self.check(self.track)

    def test_missing_track_bitrate(self):
        del self.tags['bitrate']
        self.check(self.track.copy(bitrate=None))

    def test_multiple_track_bitrate(self):
        self.tags['bitrate'].append(1234)
        self.check(self.track)

    def test_missing_track_genre(self):
        del self.tags['genre']
        self.check(self.track.copy(genre=None))

    def test_multiple_track_genre(self):
        self.tags['genre'] = ['genre1', 'genre2']
        self.check(self.track.copy(genre='genre1; genre2'))

    def test_missing_track_date(self):
        del self.tags['date']
        self.check(self.track.copy(date=None))

    def test_multiple_track_date(self):
        self.tags['date'].append(datetime.date(2030, 1, 1))
        self.check(self.track)

    def test_missing_track_comment(self):
        del self.tags['comment']
        self.check(self.track.copy(comment=None))

    def test_multiple_track_comment(self):
        self.tags['comment'] = ['comment1', 'comment2']
        self.check(self.track.copy(comment='comment1; comment2'))

    def test_missing_track_artist_name(self):
        del self.tags['artist']
        self.check(self.track.copy(artists=[]))

    def test_multiple_track_artist_name(self):
        self.tags['artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        self.check(self.track.copy(artists=artists))

    def test_missing_track_artist_musicbrainz_id(self):
        del self.tags['musicbrainz-artistid']
        artist = list(self.track.artists)[0].copy(musicbrainz_id=None)
        self.check(self.track.copy(artists=[artist]))

    def test_multiple_track_artist_musicbrainz_id(self):
        self.tags['musicbrainz-artistid'].append('id')
        self.check(self.track)

    def test_missing_track_composer_name(self):
        del self.tags['composer']
        self.check(self.track.copy(composers=[]))

    def test_multiple_track_composer_name(self):
        self.tags['composer'] = ['composer1', 'composer2']
        composers = [Artist(name='composer1'), Artist(name='composer2')]
        self.check(self.track.copy(composers=composers))

    def test_missing_track_performer_name(self):
        del self.tags['performer']
        self.check(self.track.copy(performers=[]))

    def test_multiple_track_performe_name(self):
        self.tags['performer'] = ['performer1', 'performer2']
        performers = [Artist(name='performer1'), Artist(name='performer2')]
        self.check(self.track.copy(performers=performers))

    def test_missing_album_name(self):
        del self.tags['album']
        self.check(self.track.copy(album=None))

    def test_multiple_album_name(self):
        self.tags['album'].append('album2')
        self.check(self.track)

    def test_missing_album_musicbrainz_id(self):
        del self.tags['musicbrainz-albumid']
        album = self.track.album.copy(musicbrainz_id=None,
                                      images=[])
        self.check(self.track.copy(album=album))

    def test_multiple_album_musicbrainz_id(self):
        self.tags['musicbrainz-albumid'].append('id')
        self.check(self.track)

    def test_missing_album_num_tracks(self):
        del self.tags['track-count']
        album = self.track.album.copy(num_tracks=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_num_tracks(self):
        self.tags['track-count'].append(9)
        self.check(self.track)

    def test_missing_album_num_discs(self):
        del self.tags['album-disc-count']
        album = self.track.album.copy(num_discs=None)
        self.check(self.track.copy(album=album))

    def test_multiple_album_num_discs(self):
        self.tags['album-disc-count'].append(9)
        self.check(self.track)

    def test_missing_album_artist_name(self):
        del self.tags['album-artist']
        album = self.track.album.copy(artists=[])
        self.check(self.track.copy(album=album))

    def test_multiple_album_artist_name(self):
        self.tags['album-artist'] = ['name1', 'name2']
        artists = [Artist(name='name1'), Artist(name='name2')]
        album = self.track.album.copy(artists=artists)
        self.check(self.track.copy(album=album))

    def test_missing_album_artist_musicbrainz_id(self):
        del self.tags['musicbrainz-albumartistid']
        albumartist = list(self.track.album.artists)[0]
        albumartist = albumartist.copy(musicbrainz_id=None)
        album = self.track.album.copy(artists=[albumartist])
        self.check(self.track.copy(album=album))

    def test_multiple_album_artist_musicbrainz_id(self):
        self.tags['musicbrainz-albumartistid'].append('id')
        self.check(self.track)

    def test_stream_organization_track_name(self):
        del self.tags['title']
        self.tags['organization'] = ['organization']
        self.check(self.track.copy(name='organization'))

    def test_multiple_organization_track_name(self):
        del self.tags['title']
        self.tags['organization'] = ['organization1', 'organization2']
        self.check(self.track.copy(name='organization1; organization2'))

    # TODO: combine all comment types?
    def test_stream_location_track_comment(self):
        del self.tags['comment']
        self.tags['location'] = ['location']
        self.check(self.track.copy(comment='location'))

    def test_multiple_location_track_comment(self):
        del self.tags['comment']
        self.tags['location'] = ['location1', 'location2']
        self.check(self.track.copy(comment='location1; location2'))

    def test_stream_copyright_track_comment(self):
        del self.tags['comment']
        self.tags['copyright'] = ['copyright']
        self.check(self.track.copy(comment='copyright'))

    def test_multiple_copyright_track_comment(self):
        del self.tags['comment']
        self.tags['copyright'] = ['copyright1', 'copyright2']
        self.check(self.track.copy(comment='copyright1; copyright2'))

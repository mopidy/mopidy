from __future__ import absolute_import, unicode_literals

import collections
import datetime
import logging
import numbers

from mopidy import compat
from mopidy.internal import log
from mopidy.internal.gi import GLib, Gst
from mopidy.models import Album, Artist, Track


logger = logging.getLogger(__name__)


def convert_taglist(taglist):
    """Convert a :class:`Gst.TagList` to plain Python types.

    Knows how to convert:

    - Dates
    - Buffers
    - Numbers
    - Strings
    - Booleans

    Unknown types will be ignored and trace logged. Tag keys are all strings
    defined as part GStreamer under GstTagList_.

    .. _GstTagList: https://developer.gnome.org/gstreamer/stable/\
gstreamer-GstTagList.html

    :param taglist: A GStreamer taglist to be converted.
    :type taglist: :class:`Gst.TagList`
    :rtype: dictionary of tag keys with a list of values.
    """
    result = collections.defaultdict(list)

    for n in range(taglist.n_tags()):
        tag = taglist.nth_tag_name(n)

        for i in range(taglist.get_tag_size(tag)):
            value = taglist.get_value_index(tag, i)

            if isinstance(value, GLib.Date):
                try:
                    date = datetime.date(
                        value.get_year(), value.get_month(), value.get_day())
                    result[tag].append(date.isoformat().decode('utf-8'))
                except ValueError:
                    logger.debug(
                        'Ignoring dodgy date value: %d-%d-%d',
                        value.get_year(), value.get_month(), value.get_day())
            elif isinstance(value, Gst.DateTime):
                result[tag].append(value.to_iso8601_string().decode('utf-8'))
            elif isinstance(value, bytes):
                result[tag].append(value.decode('utf-8', 'replace'))
            elif isinstance(value, (compat.text_type, bool, numbers.Number)):
                result[tag].append(value)
            elif isinstance(value, Gst.Sample):
                data = _extract_sample_data(value)
                if data:
                    result[tag].append(data)
            else:
                logger.log(
                    log.TRACE_LOG_LEVEL,
                    'Ignoring unknown tag data: %r = %r', tag, value)

    # TODO: dict(result) to not leak the defaultdict, or just use setdefault?
    return result


def _extract_sample_data(sample):
    buf = sample.get_buffer()
    if not buf:
        return None
    return buf.extract_dup(0, buf.get_size())


# TODO: split based on "stream" and "track" based conversion? i.e. handle data
# from radios in it's own helper instead?
def convert_tags_to_track(tags):
    """Convert our normalized tags to a track.

    :param  tags: dictionary of tag keys with a list of values
    :type tags: :class:`dict`
    :rtype: :class:`mopidy.models.Track`
    """
    album_kwargs = {}
    track_kwargs = {}

    track_kwargs['composers'] = _artists(tags, Gst.TAG_COMPOSER)
    track_kwargs['performers'] = _artists(tags, Gst.TAG_PERFORMER)
    track_kwargs['artists'] = _artists(tags, Gst.TAG_ARTIST,
                                       'musicbrainz-artistid',
                                       'musicbrainz-sortname')
    album_kwargs['artists'] = _artists(
        tags, Gst.TAG_ALBUM_ARTIST, 'musicbrainz-albumartistid')

    track_kwargs['genre'] = '; '.join(tags.get(Gst.TAG_GENRE, []))
    track_kwargs['name'] = '; '.join(tags.get(Gst.TAG_TITLE, []))
    if not track_kwargs['name']:
        track_kwargs['name'] = '; '.join(tags.get(Gst.TAG_ORGANIZATION, []))

    track_kwargs['comment'] = '; '.join(tags.get('comment', []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(Gst.TAG_LOCATION, []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(Gst.TAG_COPYRIGHT, []))

    track_kwargs['track_no'] = tags.get(Gst.TAG_TRACK_NUMBER, [None])[0]
    track_kwargs['disc_no'] = tags.get(Gst.TAG_ALBUM_VOLUME_NUMBER, [None])[0]
    track_kwargs['bitrate'] = tags.get(Gst.TAG_BITRATE, [None])[0]
    track_kwargs['musicbrainz_id'] = tags.get('musicbrainz-trackid', [None])[0]

    album_kwargs['name'] = tags.get(Gst.TAG_ALBUM, [None])[0]
    album_kwargs['num_tracks'] = tags.get(Gst.TAG_TRACK_COUNT, [None])[0]
    album_kwargs['num_discs'] = tags.get(Gst.TAG_ALBUM_VOLUME_COUNT, [None])[0]
    album_kwargs['musicbrainz_id'] = tags.get('musicbrainz-albumid', [None])[0]

    album_kwargs['date'] = tags.get(Gst.TAG_DATE, [None])[0]
    if not album_kwargs['date']:
        datetime = tags.get(Gst.TAG_DATE_TIME, [None])[0]
        if datetime is not None:
            album_kwargs['date'] = datetime.split('T')[0]
    track_kwargs['date'] = album_kwargs['date']

    # Clear out any empty values we found
    track_kwargs = {k: v for k, v in track_kwargs.items() if v}
    album_kwargs = {k: v for k, v in album_kwargs.items() if v}

    # Only bother with album if we have a name to show.
    if album_kwargs.get('name'):
        track_kwargs['album'] = Album(**album_kwargs)

    return Track(**track_kwargs)


def _artists(tags, artist_name, artist_id=None, artist_sortname=None):
    # Name missing, don't set artist
    if not tags.get(artist_name):
        return None

    # One artist name and either id or sortname, include all available fields
    if len(tags[artist_name]) == 1 and \
            (artist_id in tags or artist_sortname in tags):
        attrs = {'name': tags[artist_name][0]}
        if artist_id in tags:
            attrs['musicbrainz_id'] = tags[artist_id][0]
        if artist_sortname in tags:
            attrs['sortname'] = tags[artist_sortname][0]
        return [Artist(**attrs)]

    # Multiple artist, provide artists with name only to avoid ambiguity.
    return [Artist(name=name) for name in tags[artist_name]]

from __future__ import absolute_import, unicode_literals

import datetime
import logging
import numbers

import pygst
pygst.require('0.10')
import gst  # noqa

from mopidy import compat
from mopidy.models import Album, Artist, Track

logger = logging.getLogger(__name__)


def calculate_duration(num_samples, sample_rate):
    """Determine duration of samples using GStreamer helper for precise
    math."""
    return gst.util_uint64_scale(num_samples, gst.SECOND, sample_rate)


def create_buffer(data, capabilites=None, timestamp=None, duration=None):
    """Create a new GStreamer buffer based on provided data.

    Mainly intended to keep gst imports out of non-audio modules.
    """
    buffer_ = gst.Buffer(data)
    if capabilites:
        if isinstance(capabilites, compat.string_types):
            capabilites = gst.caps_from_string(capabilites)
        buffer_.set_caps(capabilites)
    if timestamp:
        buffer_.timestamp = timestamp
    if duration:
        buffer_.duration = duration
    return buffer_


def millisecond_to_clocktime(value):
    """Convert a millisecond time to internal GStreamer time."""
    return value * gst.MSECOND


def clocktime_to_millisecond(value):
    """Convert an internal GStreamer time to millisecond time."""
    return value // gst.MSECOND


def supported_uri_schemes(uri_schemes):
    """Determine which URIs we can actually support from provided whitelist.

    :param uri_schemes: list/set of URIs to check support for.
    :type uri_schemes: list or set or URI schemes as strings.
    :rtype: set of URI schemes we can support via this GStreamer install.
    """
    supported_schemes = set()
    registry = gst.registry_get_default()

    for factory in registry.get_feature_list(gst.TYPE_ELEMENT_FACTORY):
        for uri in factory.get_uri_protocols():
            if uri in uri_schemes:
                supported_schemes.add(uri)

    return supported_schemes


def _artists(tags, artist_name, artist_id=None):
    # Name missing, don't set artist
    if not tags.get(artist_name):
        return None
    # One artist name and id, provide artist with id.
    if len(tags[artist_name]) == 1 and artist_id in tags:
        return [Artist(name=tags[artist_name][0],
                       musicbrainz_id=tags[artist_id][0])]
    # Multiple artist, provide artists without id.
    return [Artist(name=name) for name in tags[artist_name]]


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

    track_kwargs['composers'] = _artists(tags, gst.TAG_COMPOSER)
    track_kwargs['performers'] = _artists(tags, gst.TAG_PERFORMER)
    track_kwargs['artists'] = _artists(
        tags, gst.TAG_ARTIST, 'musicbrainz-artistid')
    album_kwargs['artists'] = _artists(
        tags, gst.TAG_ALBUM_ARTIST, 'musicbrainz-albumartistid')

    track_kwargs['genre'] = '; '.join(tags.get(gst.TAG_GENRE, []))
    track_kwargs['name'] = '; '.join(tags.get(gst.TAG_TITLE, []))
    if not track_kwargs['name']:
        track_kwargs['name'] = '; '.join(tags.get(gst.TAG_ORGANIZATION, []))

    track_kwargs['comment'] = '; '.join(tags.get('comment', []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(gst.TAG_LOCATION, []))
    if not track_kwargs['comment']:
        track_kwargs['comment'] = '; '.join(tags.get(gst.TAG_COPYRIGHT, []))

    track_kwargs['track_no'] = tags.get(gst.TAG_TRACK_NUMBER, [None])[0]
    track_kwargs['disc_no'] = tags.get(gst.TAG_ALBUM_VOLUME_NUMBER, [None])[0]
    track_kwargs['bitrate'] = tags.get(gst.TAG_BITRATE, [None])[0]
    track_kwargs['musicbrainz_id'] = tags.get('musicbrainz-trackid', [None])[0]

    album_kwargs['name'] = tags.get(gst.TAG_ALBUM, [None])[0]
    album_kwargs['num_tracks'] = tags.get(gst.TAG_TRACK_COUNT, [None])[0]
    album_kwargs['num_discs'] = tags.get(gst.TAG_ALBUM_VOLUME_COUNT, [None])[0]
    album_kwargs['musicbrainz_id'] = tags.get('musicbrainz-albumid', [None])[0]

    if tags.get(gst.TAG_DATE) and tags.get(gst.TAG_DATE)[0]:
        track_kwargs['date'] = tags[gst.TAG_DATE][0].isoformat()

    # Clear out any empty values we found
    track_kwargs = {k: v for k, v in track_kwargs.items() if v}
    album_kwargs = {k: v for k, v in album_kwargs.items() if v}

    # Only bother with album if we have a name to show.
    if album_kwargs.get('name'):
        track_kwargs['album'] = Album(**album_kwargs)

    return Track(**track_kwargs)


def setup_proxy(element, config):
    """Configure a GStreamer element with proxy settings.

    :param element: element to setup proxy in.
    :type element: :class:`gst.GstElement`
    :param config: proxy settings to use.
    :type config: :class:`dict`
    """
    if not hasattr(element.props, 'proxy') or not config.get('hostname'):
        return

    proxy = "%s://%s:%d" % (config.get('scheme', 'http'),
                            config.get('hostname'),
                            config.get('port', 80))

    element.set_property('proxy', proxy)
    element.set_property('proxy-id', config.get('username'))
    element.set_property('proxy-pw', config.get('password'))


def convert_taglist(taglist):
    """Convert a :class:`gst.Taglist` to plain Python types.

    Knows how to convert:

    - Dates
    - Buffers
    - Numbers
    - Strings
    - Booleans

    Unknown types will be ignored and debug logged. Tag keys are all strings
    defined as part GStreamer under GstTagList_.

    .. _GstTagList: http://gstreamer.freedesktop.org/data/doc/gstreamer/\
0.10.36/gstreamer/html/gstreamer-GstTagList.html

    :param taglist: A GStreamer taglist to be converted.
    :type taglist: :class:`gst.Taglist`
    :rtype: dictionary of tag keys with a list of values.
    """
    result = {}

    # Taglists are not really dicts, hence the lack of .items() and
    # explicit use of .keys()
    for key in taglist.keys():
        result.setdefault(key, [])

        values = taglist[key]
        if not isinstance(values, list):
            values = [values]

        for value in values:
            if isinstance(value, gst.Date):
                try:
                    date = datetime.date(value.year, value.month, value.day)
                    result[key].append(date)
                except ValueError:
                    logger.debug('Ignoring invalid date: %r = %r', key, value)
            elif isinstance(value, gst.Buffer):
                result[key].append(bytes(value))
            elif isinstance(value, (basestring, bool, numbers.Number)):
                result[key].append(value)
            else:
                logger.debug('Ignoring unknown data: %r = %r', key, value)

    return result

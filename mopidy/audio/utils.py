from __future__ import absolute_import, unicode_literals

import collections
import logging
import numbers

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

from mopidy import compat, httpclient
from mopidy.models import Album, Artist, Track

logger = logging.getLogger(__name__)


def calculate_duration(num_samples, sample_rate):
    """Determine duration of samples using GStreamer helper for precise
    math."""
    return Gst.util_uint64_scale(num_samples, Gst.SECOND, sample_rate)


def create_buffer(data, capabilites=None, timestamp=None, duration=None):
    """Create a new GStreamer buffer based on provided data.

    Mainly intended to keep gst imports out of non-audio modules.

    .. versionchanged:: 1.2
        ``capabilites`` argument is no longer in use
    """
    if not data:
        raise ValueError(
            'Cannot create buffer without data: length=%d' % len(data))
    buffer_ = Gst.Buffer.new_wrapped(data)
    if timestamp is not None:
        buffer_.pts = timestamp
    if duration is not None:
        buffer_.duration = duration
    return buffer_


def millisecond_to_clocktime(value):
    """Convert a millisecond time to internal GStreamer time."""
    return value * Gst.MSECOND


def clocktime_to_millisecond(value):
    """Convert an internal GStreamer time to millisecond time."""
    return value // Gst.MSECOND


def supported_uri_schemes(uri_schemes):
    """Determine which URIs we can actually support from provided whitelist.

    :param uri_schemes: list/set of URIs to check support for.
    :type uri_schemes: list or set or URI schemes as strings.
    :rtype: set of URI schemes we can support via this GStreamer install.
    """
    supported_schemes = set()
    registry = Gst.Registry.get()

    for factory in registry.get_feature_list(Gst.ElementFactory):
        for uri in factory.get_uri_protocols():
            if uri in uri_schemes:
                supported_schemes.add(uri)

    return supported_schemes


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

    if tags.get(Gst.TAG_DATE) and tags.get(Gst.TAG_DATE)[0]:
        track_kwargs['date'] = tags[Gst.TAG_DATE][0].isoformat()

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
    :type element: :class:`Gst.GstElement`
    :param config: proxy settings to use.
    :type config: :class:`dict`
    """
    if not hasattr(element.props, 'proxy') or not config.get('hostname'):
        return

    element.set_property('proxy', httpclient.format_proxy(config, auth=False))
    element.set_property('proxy-id', config.get('username'))
    element.set_property('proxy-pw', config.get('password'))


def convert_taglist(taglist):
    """Convert a :class:`Gst.TagList` to plain Python types.

    Knows how to convert:

    - Dates
    - Buffers
    - Numbers
    - Strings
    - Booleans

    Unknown types will be ignored and debug logged. Tag keys are all strings
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

            if isinstance(value, Gst.DateTime):
                result[tag].append(value.to_iso8601_string())
            if isinstance(value, (compat.string_types, bool, numbers.Number)):
                result[tag].append(value)
            else:
                logger.debug('Ignoring unknown tag data: %r = %r', tag, value)

    return result


class Signals(object):

    """Helper for tracking gobject signal registrations"""

    def __init__(self):
        self._ids = {}

    def connect(self, element, event, func, *args):
        """Connect a function + args to signal event on an element.

        Each event may only be handled by one callback in this implementation.
        """
        assert (element, event) not in self._ids
        self._ids[(element, event)] = element.connect(event, func, *args)

    def disconnect(self, element, event):
        """Disconnect whatever handler we have for and element+event pair.

        Does nothing it the handler has already been removed.
        """
        signal_id = self._ids.pop((element, event), None)
        if signal_id is not None:
            element.disconnect(signal_id)

    def clear(self):
        """Clear all registered signal handlers."""
        for element, event in self._ids.keys():
            element.disconnect(self._ids.pop((element, event)))

from __future__ import unicode_literals

import logging
import datetime

import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst

from mopidy import settings
from mopidy.frontends.mpd import translator as mpd_translator
from mopidy.models import Track, Artist, Album
from mopidy.utils import log, path


def main():
    log.setup_root_logger()
    log.setup_console_logging(2)

    tracks = []

    def store(data):
        track = translator(data)
        tracks.append(track)
        logging.debug('Added %s', track.uri)

    def debug(uri, error, debug):
        logging.error('Failed %s: %s - %s', uri, error, debug)

    logging.info('Scanning %s', settings.LOCAL_MUSIC_PATH)
    scanner = Scanner(settings.LOCAL_MUSIC_PATH, store, debug)
    try:
        scanner.start()
    except KeyboardInterrupt:
        scanner.stop()

    logging.info('Done')

    for row in mpd_translator.tracks_to_tag_cache_format(tracks):
        if len(row) == 1:
            print ('%s' % row).encode('utf-8')
        else:
            print ('%s: %s' % row).encode('utf-8')


def translator(data):
    albumartist_kwargs = {}
    album_kwargs = {}
    artist_kwargs = {}
    track_kwargs = {}

    def _retrieve(source_key, target_key, target):
        if source_key in data:
            target[target_key] = data[source_key]

    _retrieve(gst.TAG_ALBUM, 'name', album_kwargs)
    _retrieve(gst.TAG_TRACK_COUNT, 'num_tracks', album_kwargs)
    _retrieve(gst.TAG_ARTIST, 'name', artist_kwargs)

    if gst.TAG_DATE in data and data[gst.TAG_DATE]:
        date = data[gst.TAG_DATE]
        try:
            date = datetime.date(date.year, date.month, date.day)
        except ValueError:
            pass  # Ignore invalid dates
        else:
            track_kwargs['date'] = date.isoformat()

    _retrieve(gst.TAG_TITLE, 'name', track_kwargs)
    _retrieve(gst.TAG_TRACK_NUMBER, 'track_no', track_kwargs)

    # Following keys don't seem to have TAG_* constant.
    _retrieve('album-artist', 'name', albumartist_kwargs)
    _retrieve('musicbrainz-trackid', 'musicbrainz_id', track_kwargs)
    _retrieve('musicbrainz-artistid', 'musicbrainz_id', artist_kwargs)
    _retrieve('musicbrainz-albumid', 'musicbrainz_id', album_kwargs)
    _retrieve(
        'musicbrainz-albumartistid', 'musicbrainz_id', albumartist_kwargs)

    if albumartist_kwargs:
        album_kwargs['artists'] = [Artist(**albumartist_kwargs)]

    track_kwargs['uri'] = data['uri']
    track_kwargs['length'] = data[gst.TAG_DURATION]
    track_kwargs['album'] = Album(**album_kwargs)
    track_kwargs['artists'] = [Artist(**artist_kwargs)]

    return Track(**track_kwargs)


class Scanner(object):
    def __init__(self, folder, data_callback, error_callback=None):
        self.data = {}
        self.files = path.find_files(folder)
        self.data_callback = data_callback
        self.error_callback = error_callback
        self.loop = gobject.MainLoop()

        self.fakesink = gst.element_factory_make('fakesink')
        self.fakesink.set_property('signal-handoffs', True)
        self.fakesink.connect('handoff', self.process_handoff)

        self.uribin = gst.element_factory_make('uridecodebin')
        self.uribin.set_property('caps', gst.Caps(b'audio/x-raw-int'))
        self.uribin.connect('pad-added', self.process_new_pad)

        self.pipe = gst.element_factory_make('pipeline')
        self.pipe.add(self.uribin)
        self.pipe.add(self.fakesink)

        bus = self.pipe.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.process_application)
        bus.connect('message::tag', self.process_tags)
        bus.connect('message::error', self.process_error)

    def process_handoff(self, fakesink, buffer_, pad):
        # When this function is called the first buffer has reached the end of
        # the pipeline, and we can continue with the next track. Since we're
        # in another thread, we send a message back to the main thread using
        # the bus.
        structure = gst.Structure('handoff')
        message = gst.message_new_application(fakesink, structure)
        bus = self.pipe.get_bus()
        bus.post(message)

    def process_new_pad(self, source, pad):
        pad.link(self.fakesink.get_pad('sink'))

    def process_application(self, bus, message):
        if message.src != self.fakesink:
            return

        if message.structure.get_name() != 'handoff':
            return

        self.data['uri'] = unicode(self.uribin.get_property('uri'))
        self.data[gst.TAG_DURATION] = self.get_duration()

        try:
            self.data_callback(self.data)
            self.next_uri()
        except KeyboardInterrupt:
            self.stop()

    def process_tags(self, bus, message):
        taglist = message.parse_tag()

        for key in taglist.keys():
            # XXX: For some crazy reason some wma files spit out lists here,
            # not sure if this is due to better data in headers or wma being
            # stupid. So ugly hack for now :/
            if type(taglist[key]) is list:
                self.data[key] = taglist[key][0]
            else:
                self.data[key] = taglist[key]

    def process_error(self, bus, message):
        if self.error_callback:
            uri = self.uribin.get_property('uri')
            error, debug = message.parse_error()
            self.error_callback(uri, error, debug)
        self.next_uri()

    def get_duration(self):
        self.pipe.get_state()  # Block until state change is done.
        try:
            return self.pipe.query_duration(
                gst.FORMAT_TIME, None)[0] // gst.MSECOND
        except gst.QueryError:
            return None

    def next_uri(self):
        self.data = {}
        try:
            uri = path.path_to_uri(self.files.next())
        except StopIteration:
            self.stop()
            return False
        self.pipe.set_state(gst.STATE_NULL)
        self.uribin.set_property('uri', uri)
        self.pipe.set_state(gst.STATE_PLAYING)
        return True

    def start(self):
        if self.next_uri():
            self.loop.run()

    def stop(self):
        self.pipe.set_state(gst.STATE_NULL)
        self.loop.quit()

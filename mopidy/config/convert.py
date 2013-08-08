from __future__ import unicode_literals

import io
import os.path
import sys

from mopidy import config as config_lib, ext
from mopidy.utils import path


def load():
    settings_file = path.expand_path(b'$XDG_CONFIG_DIR/mopidy/settings.py')
    print 'Checking %s' % settings_file

    setting_globals = {}
    try:
        execfile(settings_file, setting_globals)
    except Exception as e:
        print 'Problem loading settings: %s' % e
    return setting_globals


def convert(settings):
    config = {}

    def helper(confval, setting_name):
        if settings.get(setting_name) is not None:
            section, key = confval.split('/')
            config.setdefault(section, {})[key] = settings[setting_name]

    # Perform all the simple mappings using our helper:

    helper('logging/console_format', 'CONSOLE_LOG_FORMAT')
    helper('logging/debug_format', 'DEBUG_LOG_FORMAT')
    helper('logging/debug_file', 'DEBUG_LOG_FILENAME')

    helper('audio/mixer', 'MIXER')
    helper('audio/mixer_track', 'MIXER_TRACK')
    helper('audio/output', 'OUTPUT')

    helper('proxy/hostname', 'SPOTIFY_PROXY_HOST')
    helper('proxy/port', 'SPOTIFY_PROXY_PORT')
    helper('proxy/username', 'SPOTIFY_PROXY_USERNAME')
    helper('proxy/password', 'SPOTIFY_PROXY_PASSWORD')

    helper('local/media_dir', 'LOCAL_MUSIC_PATH')
    helper('local/playlists_dir', 'LOCAL_PLAYLIST_PATH')
    helper('local/tag_cache_file', 'LOCAL_TAG_CACHE_FILE')

    helper('spotify/username', 'SPOTIFY_USERNAME')
    helper('spotify/password', 'SPOTIFY_PASSWORD')
    helper('spotify/bitrate', 'SPOTIFY_BITRATE')
    helper('spotify/timeout', 'SPOTIFY_TIMEOUT')
    helper('spotify/cache_dir', 'SPOTIFY_CACHE_PATH')

    helper('stream/protocols', 'STREAM_PROTOCOLS')

    helper('http/hostname', 'HTTP_SERVER_HOSTNAME')
    helper('http/port', 'HTTP_SERVER_PORT')
    helper('http/static_dir', 'HTTP_SERVER_STATIC_DIR')

    helper('mpd/hostname', 'MPD_SERVER_HOSTNAME')
    helper('mpd/port', 'MPD_SERVER_PORT')
    helper('mpd/password', 'MPD_SERVER_PASSWORD')
    helper('mpd/max_connections', 'MPD_SERVER_MAX_CONNECTIONS')
    helper('mpd/connection_timeout', 'MPD_SERVER_CONNECTION_TIMEOUT')

    helper('mpris/desktop_file', 'DESKTOP_FILE')

    helper('scrobbler/username', 'LASTFM_USERNAME')
    helper('scrobbler/password', 'LASTFM_PASSWORD')

    # Assume FRONTENDS/BACKENDS = None implies all enabled, otherwise disable
    # if our module path is missing from the setting.

    frontends = settings.get('FRONTENDS')
    if frontends is not None:
        if 'mopidy.frontends.http.HttpFrontend' not in frontends:
            config.setdefault('http', {})['enabled'] = False
        if 'mopidy.frontends.mpd.MpdFrontend' not in frontends:
            config.setdefault('mpd', {})['enabled'] = False
        if 'mopidy.frontends.lastfm.LastfmFrontend' not in frontends:
            config.setdefault('scrobbler', {})['enabled'] = False
        if 'mopidy.frontends.mpris.MprisFrontend' not in frontends:
            config.setdefault('mpris', {})['enabled'] = False

    backends = settings.get('BACKENDS')
    if backends is not None:
        if 'mopidy.backends.local.LocalBackend' not in backends:
            config.setdefault('local', {})['enabled'] = False
        if 'mopidy.backends.spotify.SpotifyBackend' not in backends:
            config.setdefault('spotify', {})['enabled'] = False
        if 'mopidy.backends.stream.StreamBackend' not in backends:
            config.setdefault('stream', {})['enabled'] = False

    return config


def main():
    settings = load()
    if not settings:
        return

    config = convert(settings)

    known = [
        'spotify', 'scrobbler', 'mpd', 'mpris', 'local', 'stream', 'http']
    extensions = [e for e in ext.load_extensions() if e.ext_name in known]

    print b'Converted config:\n'
    print config_lib.format(config, extensions)

    conf_file = path.expand_path(b'$XDG_CONFIG_DIR/mopidy/mopidy.conf')
    if os.path.exists(conf_file):
        print '%s exists, exiting.' % conf_file
        sys.exit(1)

    print 'Write new config to %s? [yN]' % conf_file,
    if raw_input() != 'y':
        print 'Not saving, exiting.'
        sys.exit(0)

    serialized_config = config_lib.format(config, extensions, display=False)
    with io.open(conf_file, 'wb') as filehandle:
        filehandle.write(serialized_config)
    print 'Done.'

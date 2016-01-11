# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import io

from mopidy.m3u import translator
from mopidy.models import Playlist, Ref, Track


def loads(s, basedir=b'.'):
    return translator.load_items(io.StringIO(s), basedir=basedir)


def dumps(items):
    fp = io.StringIO()
    translator.dump_items(items, fp)
    return fp.getvalue()


def test_path_to_uri():
    from mopidy.m3u.translator import path_to_uri

    assert path_to_uri(b'test') == 'm3u:test'
    assert path_to_uri(b'test.m3u') == 'm3u:test.m3u'
    assert path_to_uri(b'./test.m3u') == 'm3u:test.m3u'
    assert path_to_uri(b'foo/../test.m3u') == 'm3u:test.m3u'
    assert path_to_uri(b'Test Playlist.m3u') == 'm3u:Test%20Playlist.m3u'
    assert path_to_uri(b'test.mp3', scheme='file') == 'file:///test.mp3'


def test_latin1_path_to_uri():
    path = 'æøå.m3u'.encode('latin-1')
    assert translator.path_to_uri(path) == 'm3u:%E6%F8%E5.m3u'


def test_utf8_path_to_uri():
    path = 'æøå.m3u'.encode('utf-8')
    assert translator.path_to_uri(path) == 'm3u:%C3%A6%C3%B8%C3%A5.m3u'


def test_uri_to_path():
    from mopidy.m3u.translator import uri_to_path

    assert uri_to_path('m3u:test.m3u') == b'test.m3u'
    assert uri_to_path(b'm3u:test.m3u') == b'test.m3u'
    assert uri_to_path('m3u:Test%20Playlist.m3u') == b'Test Playlist.m3u'
    assert uri_to_path(b'm3u:Test%20Playlist.m3u') == b'Test Playlist.m3u'
    assert uri_to_path('m3u:%E6%F8%E5.m3u') == b'\xe6\xf8\xe5.m3u'
    assert uri_to_path(b'm3u:%E6%F8%E5.m3u') == b'\xe6\xf8\xe5.m3u'
    assert uri_to_path('file:///test.mp3') == b'/test.mp3'
    assert uri_to_path(b'file:///test.mp3') == b'/test.mp3'


def test_name_from_path():
    from mopidy.m3u.translator import name_from_path

    assert name_from_path(b'test') == 'test'
    assert name_from_path(b'test.m3u') == 'test'
    assert name_from_path(b'../test.m3u') == 'test'


def test_path_from_name():
    from mopidy.m3u.translator import path_from_name

    assert path_from_name('test') == b'test'
    assert path_from_name('test', '.m3u') == b'test.m3u'
    assert path_from_name('foo/bar', sep='-') == b'foo-bar'


def test_path_to_ref():
    from mopidy.m3u.translator import path_to_ref

    assert path_to_ref(b'test.m3u') == Ref.playlist(
        uri='m3u:test.m3u', name='test'
    )
    assert path_to_ref(b'Test Playlist.m3u') == Ref.playlist(
        uri='m3u:Test%20Playlist.m3u', name='Test Playlist'
    )


def test_load_items():
    assert loads('') == []

    assert loads('test.mp3', basedir=b'/playlists') == [
        Ref.track(uri='file:///playlists/test.mp3', name='test')
    ]
    assert loads('../test.mp3', basedir=b'/playlists') == [
        Ref.track(uri='file:///test.mp3', name='test')
    ]
    assert loads('/test.mp3') == [
        Ref.track(uri='file:///test.mp3', name='test')
    ]
    assert loads('file:///test.mp3') == [
        Ref.track(uri='file:///test.mp3')
    ]
    assert loads('http://example.com/stream') == [
        Ref.track(uri='http://example.com/stream')
    ]

    assert loads('#EXTM3U\n#EXTINF:42,Test\nfile:///test.mp3\n') == [
        Ref.track(uri='file:///test.mp3', name='Test')
    ]
    assert loads('#EXTM3U\n#EXTINF:-1,Test\nhttp://example.com/stream\n') == [
        Ref.track(uri='http://example.com/stream', name='Test')
    ]


def test_dump_items():
    assert dumps([]) == ''
    assert dumps([Ref.track(uri='file:///test.mp3')]) == (
        'file:///test.mp3\n'
    )
    assert dumps([Ref.track(uri='file:///test.mp3', name='test')]) == (
        '#EXTM3U\n'
        '#EXTINF:-1,test\n'
        'file:///test.mp3\n'
    )
    assert dumps([Track(uri='file:///test.mp3', name='test', length=42)]) == (
        '#EXTM3U\n'
        '#EXTINF:-1,test\n'
        'file:///test.mp3\n'
    )
    assert dumps([Track(uri='http://example.com/stream')]) == (
        'http://example.com/stream\n'
    )
    assert dumps([Track(uri='http://example.com/stream', name='Test')]) == (
        '#EXTM3U\n'
        '#EXTINF:-1,Test\n'
        'http://example.com/stream\n'
    )


def test_playlist():
    from mopidy.m3u.translator import playlist

    assert playlist(b'test.m3u') == Playlist(
        uri='m3u:test.m3u',
        name='test'
    )
    assert playlist(b'test.m3u', [Ref(uri='file:///test.mp3')], 1) == Playlist(
        uri='m3u:test.m3u',
        name='test',
        tracks=[Track(uri='file:///test.mp3')],
        last_modified=1000
    )

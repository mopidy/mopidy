# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import unittest

import pytest

from mopidy.internal import playlists


BAD = b'foobarbaz'

EXTM3U = b"""#EXTM3U
#EXTINF:123, Sample artist - Sample title
file:///tmp/foo
#EXTINF:321,Example Artist - Example \xc5\xa7\xc5\x95
file:///tmp/bar

#EXTINF:213,Some Artist - Other title
file:///tmp/baz
"""

URILIST = b"""
file:///tmp/foo
# a comment \xc5\xa7\xc5\x95
file:///tmp/bar

file:///tmp/baz
"""

PLS = b"""[Playlist]
NumberOfEntries=3
File1=file:///tmp/foo
Title1=Sample Title
Length1=123

File2=file:///tmp/bar
Title2=Example \xc5\xa7\xc5\x95
Length2=321
File3=file:///tmp/baz
Title3=Other title
Length3=213
Version=2
"""

ASX = b"""<ASX version="3.0">
  <TITLE>Example</TITLE>
  <ENTRY>
    <TITLE>Sample Title</TITLE>
    <REF href="file:///tmp/foo" />
  </ENTRY>
  <ENTRY>
    <TITLE>Example \xc5\xa7\xc5\x95</TITLE>
    <REF href="file:///tmp/bar" />
  </ENTRY>
  <ENTRY>
    <TITLE>Other title</TITLE>
    <REF href="file:///tmp/baz" />
  </ENTRY>
</ASX>
"""

SIMPLE_ASX = b"""<ASX version="3.0">
  <ENTRY href="file:///tmp/foo" />
  <ENTRY href="file:///tmp/bar" />
  <ENTRY href="file:///tmp/baz" />
</ASX>
"""

XSPF = b"""<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <trackList>
    <track>
      <title>Sample Title</title>
      <location>file:///tmp/foo</location>
    </track>
    <track>
      <title>Example \xc5\xa7\xc5\x95</title>
      <location>file:///tmp/bar</location>
    </track>
    <track>
      <title>Other title</title>
      <location>file:///tmp/baz</location>
    </track>
  </trackList>
</playlist>
"""

EXPECTED = [b'file:///tmp/foo', b'file:///tmp/bar', b'file:///tmp/baz']


@pytest.mark.parametrize('data,result', [
    (BAD, []),
    (URILIST, EXPECTED),
    (EXTM3U, EXPECTED),
    (PLS, EXPECTED),
    (ASX, EXPECTED),
    (SIMPLE_ASX, EXPECTED),
    (XSPF, EXPECTED),
])
def test_parse(data, result):
    assert playlists.parse(data) == result


class BasePlaylistTest(object):
    valid = None
    invalid = None
    detect = None
    parse = None

    def test_detect_valid_header(self):
        self.assertTrue(self.detect(self.valid))

    def test_detect_invalid_header(self):
        self.assertFalse(self.detect(self.invalid))

    def test_parse_valid_playlist(self):
        uris = list(self.parse(self.valid))
        self.assertEqual(uris, EXPECTED)

    def test_parse_invalid_playlist(self):
        uris = list(self.parse(self.invalid))
        self.assertEqual(uris, [])


class ExtM3uPlaylistTest(BasePlaylistTest, unittest.TestCase):
    valid = EXTM3U
    invalid = BAD
    detect = staticmethod(playlists.detect_extm3u_header)
    parse = staticmethod(playlists.parse_extm3u)


class PlsPlaylistTest(BasePlaylistTest, unittest.TestCase):
    valid = PLS
    invalid = BAD
    detect = staticmethod(playlists.detect_pls_header)
    parse = staticmethod(playlists.parse_pls)


class AsxPlsPlaylistTest(BasePlaylistTest, unittest.TestCase):
    valid = ASX
    invalid = BAD
    detect = staticmethod(playlists.detect_asx_header)
    parse = staticmethod(playlists.parse_asx)


class SimpleAsxPlsPlaylistTest(BasePlaylistTest, unittest.TestCase):
    valid = SIMPLE_ASX
    invalid = BAD
    detect = staticmethod(playlists.detect_asx_header)
    parse = staticmethod(playlists.parse_asx)


class XspfPlaylistTest(BasePlaylistTest, unittest.TestCase):
    valid = XSPF
    invalid = BAD
    detect = staticmethod(playlists.detect_xspf_header)
    parse = staticmethod(playlists.parse_xspf)


class UriListPlaylistTest(unittest.TestCase):
    valid = URILIST
    invalid = BAD
    parse = staticmethod(playlists.parse_urilist)

    def test_parse_valid_playlist(self):
        uris = list(self.parse(self.valid))
        self.assertEqual(uris, EXPECTED)

    def test_parse_invalid_playlist(self):
        uris = list(self.parse(self.invalid))
        self.assertEqual(uris, [])

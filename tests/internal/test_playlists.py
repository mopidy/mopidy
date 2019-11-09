import pytest

from mopidy.internal import playlists

BAD = b"foobarbaz"

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
File1="file:///tmp/foo"
Title1=Sample Title
Length1=123

File2='file:///tmp/bar'
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

EXPECTED = ["file:///tmp/foo", "file:///tmp/bar", "file:///tmp/baz"]


@pytest.mark.parametrize(
    "detect_fn, data",
    [
        (playlists.detect_extm3u_header, EXTM3U),
        (playlists.detect_pls_header, PLS),
        (playlists.detect_asx_header, ASX),
        (playlists.detect_asx_header, SIMPLE_ASX),
        (playlists.detect_xspf_header, XSPF),
    ],
)
def test_detect_from_valid_header(detect_fn, data):
    assert detect_fn(data) is True


@pytest.mark.parametrize(
    "detect_fn",
    [
        playlists.detect_extm3u_header,
        playlists.detect_pls_header,
        playlists.detect_asx_header,
        playlists.detect_asx_header,
        playlists.detect_xspf_header,
    ],
)
def test_detect_from_invalid_header(detect_fn):
    assert detect_fn(BAD) is False


@pytest.mark.parametrize(
    "parse_fn, data",
    [
        (playlists.parse_extm3u, EXTM3U),
        (playlists.parse_pls, PLS),
        (playlists.parse_asx, ASX),
        (playlists.parse_asx, SIMPLE_ASX),
        (playlists.parse_xspf, XSPF),
        (playlists.parse_urilist, URILIST),
    ],
)
def test_parse_given_format_from_valid_data(parse_fn, data):
    assert list(parse_fn(data)) == EXPECTED


@pytest.mark.parametrize(
    "parse_fn",
    [
        playlists.parse_extm3u,
        playlists.parse_pls,
        playlists.parse_asx,
        playlists.parse_xspf,
        playlists.parse_urilist,
    ],
)
def test_parse_given_format_from_invalid_data(parse_fn):
    assert list(parse_fn(BAD)) == []


@pytest.mark.parametrize("data", [URILIST, EXTM3U, PLS, ASX, SIMPLE_ASX, XSPF])
def test_parse_any_format_from_valid_data(data):
    assert playlists.parse(data) == EXPECTED


def test_parse_from_invalid_data():
    assert playlists.parse(BAD) == []

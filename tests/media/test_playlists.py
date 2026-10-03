import pytest

from mopidy.media import PlaylistEntry, parse_playlist_entries
from mopidy.models import Track

BASE_URI = "file:///tmp/"

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
Version=2

File2='file:///tmp/bar'
Title2=Example \xc5\xa7\xc5\x95
Length2=321
File3=file:///tmp/baz
Title3=Other title
Length3=213
Version=2
"""

MALFORMED_PLS_WITHOUT_NUMBER_OF_ENTRIES = b"""[Playlist]
File1=file:///tmp/foo
"""

MALFORMED_PLS_WITH_TOO_MANY_ENTRIES = b"""[Playlist]
NumberOfEntries=3
File1=file:///tmp/foo
"""

MALFORMED_PLS_WITH_TOO_FEW_ENTRIES = b"""[Playlist]
NumberOfEntries=1
File1=file:///tmp/foo
File2=file:///tmp/bar
File3=file:///tmp/baz
"""

MALFORMED_PLS_WITH_INVALID_NUMBER_OF_ENTRIES = b"""[Playlist]
NumberOfEntries=three
File1=file:///tmp/foo
"""

MALFORMED_PLS_WITH_HUGE_NUMBER_OF_ENTRIES = b"""[Playlist]
NumberOfEntries=5000000
File1=file:///tmp/foo
"""

MALFORMED_PLS_WITH_UNORDERED_ENTRIES = b"""[Playlist]
File10=file:///tmp/baz
File2=file:///tmp/bar
File1=file:///tmp/foo
"""

MALFORMED_PLS_WITH_EMPTY_ENTRIES = b"""[Playlist]
NumberOfEntries=3
File1=
File2=""
File3=file:///tmp/foo
"""

ASX_REFERENCE = b"""[Reference]
Ref1=file:///tmp/foo
Ref2=file:///tmp/bar
Ref3=file:///tmp/baz
"""

MALFORMED_ASX_REFERENCE_WITH_EMPTY_ENTRIES = b"""[Reference]
Ref1=
Ref2=""
Ref3=file:///tmp/foo
"""

ASX = b"""<ASX version="3.0">
  <TITLE>Example</TITLE>
  <ENTRY>
    <TITLE>Sample Title</TITLE>
    <DURATION VALUE="00:02:03" />
    <REF href="file:///tmp/foo" />
  </ENTRY>
  <ENTRY>
    <TITLE>Example \xc5\xa7\xc5\x95</TITLE>
    <DURATION VALUE="05:21.5" />
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
      <duration>123000</duration>
      <location>file:///tmp/foo</location>
    </track>
    <track>
      <title>Example \xc5\xa7\xc5\x95</title>
      <duration>321000</duration>
      <location>file:///tmp/bar</location>
    </track>
    <track>
      <title>Other title</title>
      <location>file:///tmp/baz</location>
    </track>
  </trackList>
</playlist>
"""

HLS_MEDIA_PLAYLIST = b"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:9.009,
segment0.ts
#EXTINF:9.009,
segment1.ts
#EXT-X-ENDLIST
"""

HLS_MASTER_PLAYLIST = b"""#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=128000,CODECS="mp4a.40.2"
low/index.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=256000,CODECS="mp4a.40.2"
high/index.m3u8
"""

DASH = b"""<?xml version="1.0" encoding="UTF-8"?>
<MPD xmlns="urn:mpeg:dash:schema:mpd:2011" type="static">
  <Period>
    <AdaptationSet mimeType="audio/mp4">
      <Representation id="1" bandwidth="128000">
        <BaseURL>audio.mp4</BaseURL>
      </Representation>
    </AdaptationSet>
  </Period>
</MPD>
"""

EXPECTED = ["file:///tmp/foo", "file:///tmp/bar", "file:///tmp/baz"]


def entry(*alternatives, name=None, length=None):
    return PlaylistEntry(
        track=Track(uri=alternatives[0], name=name, length=length),
        alternatives=alternatives,
    )


def uris(entries):
    return [entry.track.uri for entry in entries]


@pytest.mark.parametrize(
    "data",
    [URILIST, EXTM3U, PLS, ASX_REFERENCE, ASX, SIMPLE_ASX, XSPF],
)
def test_parse_any_format_from_valid_data(data):
    assert uris(parse_playlist_entries(data, base_uri=BASE_URI)) == EXPECTED


def test_parse_from_invalid_data():
    assert parse_playlist_entries(BAD, base_uri=BASE_URI) == ()


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param(
            MALFORMED_PLS_WITHOUT_NUMBER_OF_ENTRIES,
            ["file:///tmp/foo"],
            id="without-number-of-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_TOO_MANY_ENTRIES,
            ["file:///tmp/foo"],
            id="with-too-many-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_TOO_FEW_ENTRIES,
            EXPECTED,
            id="with-too-few-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_INVALID_NUMBER_OF_ENTRIES,
            ["file:///tmp/foo"],
            id="with-invalid-number-of-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_HUGE_NUMBER_OF_ENTRIES,
            ["file:///tmp/foo"],
            id="with-huge-number-of-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_UNORDERED_ENTRIES,
            EXPECTED,
            id="with-unordered-entries",
        ),
        pytest.param(
            MALFORMED_PLS_WITH_EMPTY_ENTRIES,
            ["file:///tmp/foo"],
            id="with-empty-entries",
        ),
    ],
)
def test_parse_malformed_pls(data, expected):
    assert uris(parse_playlist_entries(data, base_uri=BASE_URI)) == expected


def test_parse_malformed_asx_reference():
    assert uris(
        parse_playlist_entries(
            MALFORMED_ASX_REFERENCE_WITH_EMPTY_ENTRIES, base_uri=BASE_URI
        )
    ) == ["file:///tmp/foo"]


def test_m3u_gives_names_and_lengths():
    assert parse_playlist_entries(EXTM3U, base_uri=BASE_URI) == (
        entry("file:///tmp/foo", name="Sample artist - Sample title", length=123000),
        entry("file:///tmp/bar", name="Example Artist - Example ŧŕ", length=321000),
        entry("file:///tmp/baz", name="Some Artist - Other title", length=213000),
    )


@pytest.mark.parametrize(
    ("extinf", "name", "length"),
    [
        pytest.param("#EXTINF:-1,Radio", "Radio", None, id="unknown-length"),
        pytest.param("#EXTINF:9.5,", None, 9500, id="float-length-no-name"),
        pytest.param(
            '#EXTINF:-1 tvg-id="x" group-title="y",Radio',
            "Radio",
            None,
            id="attributes",
        ),
        pytest.param("#EXTINF:foo,Radio", "Radio", None, id="invalid-length"),
    ],
)
def test_m3u_extinf_variants(extinf, name, length):
    data = f"#EXTM3U\n{extinf}\nhttp://example.com/stream\n".encode()

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("http://example.com/stream", name=name, length=length),
    )


def test_m3u_extinf_applies_only_to_the_next_entry():
    data = b"#EXTM3U\n#EXTINF:1,One\nfile:///a\nfile:///b\n"

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("file:///a", name="One", length=1000),
        entry("file:///b"),
    )


def test_pls_gives_names_and_lengths():
    assert parse_playlist_entries(PLS, base_uri=BASE_URI) == (
        entry("file:///tmp/foo", name="Sample Title", length=123000),
        entry("file:///tmp/bar", name="Example ŧŕ", length=321000),
        entry("file:///tmp/baz", name="Other title", length=213000),
    )


def test_pls_with_leading_zeros_in_keys():
    data = b"[playlist]\nFile01=file:///a\nTitle01=A\nLength01=1\n"

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("file:///a", name="A", length=1000),
    )


def test_pls_with_unknown_length():
    data = b"[playlist]\nFile1=http://example.com/stream\nLength1=-1\n"

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("http://example.com/stream"),
    )


def test_asx_reference_gives_one_entry_for_each_ref():
    assert parse_playlist_entries(ASX_REFERENCE, base_uri=BASE_URI) == (
        entry("file:///tmp/foo"),
        entry("file:///tmp/bar"),
        entry("file:///tmp/baz"),
    )


def test_xspf_gives_names_and_lengths():
    assert parse_playlist_entries(XSPF, base_uri=BASE_URI) == (
        entry("file:///tmp/foo", name="Sample Title", length=123000),
        entry("file:///tmp/bar", name="Example ŧŕ", length=321000),
        entry("file:///tmp/baz", name="Other title"),
    )


def test_xspf_gives_all_locations_of_a_track_as_alternatives():
    data = b"""<?xml version="1.0" encoding="UTF-8"?>
<playlist version="1" xmlns="http://xspf.org/ns/0/">
  <trackList>
    <track>
      <location>http://a.example.com/stream</location>
      <location>http://b.example.com/stream</location>
    </track>
    <track>
      <title>No location</title>
    </track>
  </trackList>
</playlist>
"""

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("http://a.example.com/stream", "http://b.example.com/stream"),
    )


def test_asx_gives_names_and_lengths():
    assert parse_playlist_entries(ASX, base_uri=BASE_URI) == (
        entry("file:///tmp/foo", name="Sample Title", length=123000),
        entry("file:///tmp/bar", name="Example ŧŕ", length=321500),
        entry("file:///tmp/baz", name="Other title"),
    )


def test_asx_gives_all_refs_of_an_entry_as_alternatives():
    data = b"""<asx version="3.0">
  <entry>
    <ref HREF="http://a.example.com/stream" />
    <ref HREF="http://b.example.com/stream" />
  </entry>
  <entry>
    <title>No ref</title>
  </entry>
</asx>
"""

    assert parse_playlist_entries(data, base_uri=BASE_URI) == (
        entry("http://a.example.com/stream", "http://b.example.com/stream"),
    )


def test_asx_entryref_gives_an_entry_in_document_order():
    data = b"""<ASX VERSION="3.0">
  <ENTRY><REF HREF="http://example.com/first" /></ENTRY>
  <ENTRYREF HREF="http://example.com/nested.asx" />
  <ENTRY><REF HREF="http://example.com/last" /></ENTRY>
</ASX>
"""

    assert uris(parse_playlist_entries(data, base_uri=BASE_URI)) == [
        "http://example.com/first",
        "http://example.com/nested.asx",
        "http://example.com/last",
    ]


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(HLS_MEDIA_PLAYLIST, id="hls-media-playlist"),
        pytest.param(HLS_MASTER_PLAYLIST, id="hls-master-playlist"),
        pytest.param(
            b"#EXTM3U\n  #EXT-X-VERSION:3\nsegment0.ts\n", id="hls-indented-tag"
        ),
        pytest.param(DASH, id="dash"),
    ],
)
def test_adaptive_streams_give_no_entries(data):
    assert parse_playlist_entries(data, base_uri="http://example.com/") == ()


@pytest.mark.parametrize(
    "data",
    [
        pytest.param(b"ID3\x04\x00\x00\x00\x00\x00/x.mp3\n", id="binary"),
        pytest.param(
            b'<!DOCTYPE html>\n<html><a href="/x.mp3">x</a></html>\n', id="html"
        ),
        pytest.param(b"Not Found\n", id="text"),
        pytest.param(b"Error: page not found\n", id="text-with-colon"),
        pytest.param(b"", id="empty"),
    ],
)
def test_content_that_is_not_a_playlist_document_gives_no_entries(data):
    assert parse_playlist_entries(data, base_uri="http://example.com/") == ()


@pytest.mark.parametrize(
    "data",
    [URILIST, EXTM3U, PLS, ASX_REFERENCE, ASX, SIMPLE_ASX, XSPF, HLS_MEDIA_PLAYLIST],
)
@pytest.mark.parametrize(
    ("media_type", "uri"),
    [
        ("audio/x-mpegurl", "http://example.com/x.m3u"),
        ("application/x-mpegurl", None),
        ("audio/x-scpls; charset=UTF-8", "http://example.com/x.pls"),
        ("video/x-ms-asf", "http://example.com/x.asx"),
        (None, "http://example.com/x.wax?foo=bar"),
        ("audio/mpegurl", "http://example.com/x.m3u8"),
        ("application/vnd.apple.mpegurl", None),
        ("application/xspf+xml", "http://example.com/x.xspf"),
        ("audio/x-ms-asx", "http://example.com/x.wvx"),
        ("text/uri-list", "http://example.com/x.wmx"),
        ("audio/mpeg", "http://example.com/x.mp3"),
    ],
)
def test_hints_do_not_change_the_result(data, media_type, uri):
    without_hints = parse_playlist_entries(data, base_uri=BASE_URI)

    result = parse_playlist_entries(
        data, base_uri=BASE_URI, media_type=media_type, uri=uri
    )

    assert result == without_hints


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param(
            b"#EXTM3U\nfoo.mp3\n../bar.mp3\n/baz.mp3\nqux\n",
            [
                "http://example.com/radio/foo.mp3",
                "http://example.com/bar.mp3",
                "http://example.com/baz.mp3",
                "http://example.com/radio/qux",
            ],
            id="m3u",
        ),
        pytest.param(
            b"foo.mp3\nsub/bar\nqux\nhttp://example.com/abs\n",
            [
                "http://example.com/radio/foo.mp3",
                "http://example.com/radio/sub/bar",
                "http://example.com/abs",
            ],
            id="m3u-without-header",
        ),
        pytest.param(
            b"[playlist]\nFile1=foo.mp3\n",
            ["http://example.com/radio/foo.mp3"],
            id="pls",
        ),
        pytest.param(
            b"[Reference]\nRef1=foo.mp3\n",
            ["http://example.com/radio/foo.mp3"],
            id="asx-reference",
        ),
        pytest.param(
            b'<playlist xmlns="http://xspf.org/ns/0/"><trackList>'
            b"<track><location>foo.mp3</location></track>"
            b"</trackList></playlist>",
            ["http://example.com/radio/foo.mp3"],
            id="xspf",
        ),
        pytest.param(
            b'<asx version="3.0"><entry><ref href="foo.mp3" /></entry></asx>',
            ["http://example.com/radio/foo.mp3"],
            id="asx",
        ),
    ],
)
def test_relative_entries_are_joined_with_the_base_uri(data, expected):
    result = parse_playlist_entries(data, base_uri="http://example.com/radio/list")

    assert uris(result) == expected


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        pytest.param(
            "Some Song.mp3", "http://example.com/radio/Some%20Song.mp3", id="space"
        ),
        pytest.param(
            "Blåbær.mp3",
            "http://example.com/radio/Bl%C3%A5b%C3%A6r.mp3",
            id="non-ascii",
        ),
        pytest.param(
            "listen.pls?sid=1", "http://example.com/radio/listen.pls?sid=1", id="query"
        ),
        pytest.param("a%20b.mp3", "http://example.com/radio/a%20b.mp3", id="escape"),
    ],
)
def test_relative_paths_are_quoted_where_needed(line, expected):
    data = f"#EXTM3U\n{line}\n".encode()

    result = parse_playlist_entries(data, base_uri="http://example.com/radio/list")

    assert uris(result) == [expected]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        pytest.param("song #1.mp3", "file:///music/song%20%231.mp3", id="hash"),
        pytest.param("100%.mp3", "file:///music/100%25.mp3", id="percent"),
        pytest.param("a?b.mp3", "file:///music/a%3Fb.mp3", id="question-mark"),
        pytest.param("[live].mp3", "file:///music/%5Blive%5D.mp3", id="brackets"),
        pytest.param("/abs/a b.mp3", "file:///abs/a%20b.mp3", id="absolute"),
    ],
)
def test_relative_paths_in_a_local_playlist_are_file_paths(line, expected):
    data = f"#EXTM3U\n{line}\n".encode()

    result = parse_playlist_entries(data, base_uri="file:///music/list.m3u")

    assert uris(result) == [expected]


def test_decodes_with_the_given_encoding():
    data = "#EXTM3U\n#EXTINF:1,Blåbær\nfile:///a\n".encode("latin-1")

    result = parse_playlist_entries(data, base_uri=BASE_URI, encoding="latin-1")

    assert result == (entry("file:///a", name="Blåbær", length=1000),)


def test_replaces_bytes_that_do_not_decode():
    data = b"#EXTM3U\n#EXTINF:1,Bl\xe5b\xe6r\nfile:///a\n"

    result = parse_playlist_entries(data, base_uri=BASE_URI)

    assert result == (entry("file:///a", name="Bl�b�r", length=1000),)


def test_ignores_a_byte_order_mark():
    data = b"\xef\xbb\xbf[playlist]\nFile1=file:///a\n"

    result = parse_playlist_entries(data, base_uri=BASE_URI)

    assert result == (entry("file:///a"),)

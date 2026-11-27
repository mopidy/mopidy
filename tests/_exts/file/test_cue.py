import pathlib

import pytest

from mopidy._exts.file import cue

SHEET = """\
REM GENRE "Rock"
REM DATE 1999
REM DISCNUMBER 2
PERFORMER "The Band"
TITLE "Big Album"
FILE "Big Album.wav" WAVE
  TRACK 01 AUDIO
    TITLE "One"
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE "Two"
    PERFORMER "Guest"
    INDEX 00 03:58:50
    INDEX 01 04:00:37
  TRACK 03 AUDIO
    TITLE "Three"
    INDEX 01 08:00:00
FILE "bonus track.flac" WAVE
  TRACK 04 AUDIO
    TITLE "Bonus"
    INDEX 01 00:00:00
  TRACK 05 MODE1/2352
    INDEX 01 00:00:00
"""


def test_parse_album():
    sheet = cue.parse(SHEET)

    assert sheet.title == "Big Album"
    assert sheet.performer == "The Band"
    assert sheet.genre == "Rock"
    assert sheet.date == "1999"
    assert sheet.disc_no == 2
    assert sheet.files == ["Big Album.wav", "bonus track.flac"]


def test_parse_tracks_skips_data_tracks():
    sheet = cue.parse(SHEET)

    assert [t.number for t in sheet.tracks] == [1, 2, 3, 4]
    assert [t.title for t in sheet.tracks] == ["One", "Two", "Three", "Bonus"]


def test_track_without_performer_gets_the_album_performer():
    sheet = cue.parse(SHEET)

    assert [t.performer for t in sheet.tracks] == [
        "The Band",
        "Guest",
        "The Band",
        "The Band",
    ]


def test_tracks_end_where_the_next_track_in_the_same_file_starts():
    sheet = cue.parse(SHEET)

    # 37 frames is 493 ms. Audio in the pregap (INDEX 00) belongs to track 1.
    assert [t.start for t in sheet.tracks] == [0, 240_493, 480_000, 0]
    assert [t.end for t in sheet.tracks] == [240_493, 480_000, None, None]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("00:00:00", 0),
        ("00:01:00", 1000),
        ("01:00:00", 60_000),
        ("00:00:75", 1000),
        ("00:00:01", 13),
        ("nonsense", None),
    ],
)
def test_parse_time(value, expected):
    assert cue.parse_time(value) == expected


def test_parse_file_name_with_spaces_and_no_quotes_and_crlf():
    sheet = cue.parse(
        "FILE my album.flac WAVE\r\n  TRACK 01 AUDIO\r\n    INDEX 01 00:00:00\r\n"
    )

    assert sheet.tracks[0].file == "my album.flac"


def test_parse_without_tracks_fails():
    with pytest.raises(cue.CueError):
        cue.parse('TITLE "Nothing"\nFILE "a.flac" WAVE\n')


def test_parse_ignores_a_track_without_index_01():
    sheet = cue.parse(
        'FILE "a.flac" WAVE\n'
        "  TRACK 01 AUDIO\n    INDEX 00 00:00:00\n"
        "  TRACK 02 AUDIO\n    INDEX 01 01:00:00\n"
    )

    assert [t.number for t in sheet.tracks] == [2]


TEXT = 'TITLE "{}"\nFILE "a.flac" WAVE\n TRACK 01 AUDIO\n  INDEX 01 00:00:00\n'


@pytest.mark.parametrize(
    ("title", "encoding", "encodings"),
    [
        ("Café", "utf-8", ["utf-8"]),
        ("Café", "utf-8-sig", ["utf-8"]),
        ("Café", "utf-16", ["utf-8"]),
        ("Café", "cp1252", ["utf-8", "cp1252"]),
        ("Привет мир", "utf-8", ["utf-8"]),
        ("Привет мир", "cp1251", ["utf-8", "cp1251"]),
        ("日本語のタイトル", "utf-8", ["utf-8"]),
        ("日本語のタイトル", "shift_jis", ["utf-8", "shift_jis"]),
        ("中文标题", "gbk", ["utf-8", "gbk"]),
        ("한국어 제목", "euc_kr", ["utf-8", "euc_kr"]),
    ],
)
def test_decode(title, encoding, encodings):
    data = TEXT.format(title).encode(encoding)

    assert cue.parse_bytes(data, encodings).title == title


def test_decode_prefers_utf8_over_the_configured_encodings():
    data = TEXT.format("Привет").encode("utf-8")

    assert cue.parse_bytes(data, ["cp1251"]).title == "Привет"


def test_decode_with_unknown_encoding_is_skipped():
    data = TEXT.format("Привет").encode("cp1251")

    assert cue.parse_bytes(data, ["no-such-encoding", "cp1251"]).title == "Привет"


def test_decode_that_nothing_matches_replaces_bad_bytes():
    data = TEXT.format("Привет").encode("cp1251")

    assert "\ufffd" in cue.parse_bytes(data, ["utf-8"]).title


@pytest.fixture
def cue_path(tmp_path: pathlib.Path) -> pathlib.Path:
    (tmp_path / "Album.FLAC").write_bytes(b"")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "track.flac").write_bytes(b"")
    path = tmp_path / "album.cue"
    path.write_text("")
    return path


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Album.FLAC", "Album.FLAC"),
        ("album.flac", "Album.FLAC"),
        ("Album.wav", "Album.FLAC"),
        ("C:\\Music\\Album.wav", "Album.FLAC"),
        ("/home/someone/Album.wav", "Album.FLAC"),
        ("sub\\track.flac", "track.flac"),
        ("missing.flac", None),
        ("../secret.flac", None),
    ],
)
def test_find_audio_file(cue_path, name, expected):
    found = cue.find_audio_file(cue_path, name)

    assert (found.name if found else None) == expected

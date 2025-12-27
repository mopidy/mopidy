from pathlib import Path

from cyclopts import Token

from mopidy._app import cli


def test_config_paths_converter() -> None:
    # Single path
    assert cli.config_paths_converter(
        list[Path],
        [Token(value="~/.config/mopidy/mopidy.conf")],
    ) == [
        Path("~/.config/mopidy/mopidy.conf").expanduser(),
    ]

    # Multiple paths separated by colon
    assert cli.config_paths_converter(
        list[Path],
        [Token(value="~/.config/mopidy/mopidy.conf:/etc/mopidy/mopidy.conf")],
    ) == [
        Path("~/.config/mopidy/mopidy.conf").expanduser(),
        Path("/etc/mopidy/mopidy.conf"),
    ]

    # Multiple paths via repeated --config parameters
    assert cli.config_paths_converter(
        list[Path],
        [
            Token(value="~/.config/mopidy/mopidy.conf"),
            Token(value="/etc/mopidy/mopidy.conf"),
        ],
    ) == [
        Path("~/.config/mopidy/mopidy.conf").expanduser(),
        Path("/etc/mopidy/mopidy.conf"),
    ]


def test_config_overrides_converter() -> None:
    assert cli.config_overrides_converter(
        dict[str, dict[str, str]],
        [
            Token(value="section1/keyA=value1A"),
            Token(value="section2/keyA=value2A"),
            Token(value="section1/keyB=value1B"),
        ],
    ) == {
        "section1": {
            "keyA": "value1A",
            "keyB": "value1B",
        },
        "section2": {
            "keyA": "value2A",
        },
    }

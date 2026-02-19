from pathlib import Path

import pytest

import mopidy
from mopidy._app.config import ConfigLoader
from mopidy._app.extensions import ExtensionManager


def test_load_raw_config():
    config_loader = ConfigLoader.only_defaults(extensions=None)

    assert config_loader.raw_config == {
        "audio": {
            "buffer_time": "",
            "mixer": "software",
            "mixer_volume": "",
            "output": "autoaudiosink",
        },
        "core": {
            "cache_dir": "$XDG_CACHE_DIR/mopidy",
            "config_dir": "$XDG_CONFIG_DIR/mopidy",
            "data_dir": "$XDG_DATA_DIR/mopidy",
            "max_tracklist_length": "10000",
            "restore_state": "false",
        },
        "logging": {
            "color": "true",
            "config_file": "",
            "format": (
                "[dim green]%(threadName)s[/dim green] "
                "[dim yellow]%(name)s[/dim yellow]\\n%(message)s"
            ),
            "verbosity": "0",
        },
        "proxy": {
            "hostname": "",
            "password": "",
            "port": "",
            "scheme": "",
            "username": "",
        },
    }


def test_validate_config():
    config_loader = ConfigLoader.only_defaults(extensions=None)
    config_manager = config_loader.validate()

    assert config_manager.config == {
        "audio": {
            "buffer_time": None,
            "mixer": "software",
            "mixer_volume": None,
            "output": "autoaudiosink",
        },
        "core": {
            "cache_dir": str(Path("~/.cache/mopidy").expanduser()),
            "config_dir": str(Path("~/.config/mopidy").expanduser()),
            "data_dir": str(Path("~/.local/share/mopidy").expanduser()),
            "max_tracklist_length": 10000,
            "restore_state": False,
        },
        "logging": {
            "color": True,
            "config_file": None,
            "format": (
                "[dim green]%(threadName)s[/dim green] "
                "[dim yellow]%(name)s[/dim yellow]\n%(message)s"
            ),
            "verbosity": 0,
        },
        "proxy": {
            "hostname": None,
            "password": None,
            "port": None,
            "scheme": None,
            "username": None,
        },
    }


def test_format_config():
    config_loader = ConfigLoader.only_defaults(extensions=None)
    config_manager = config_loader.validate()

    assert config_manager.format(
        with_header=True,
        hide_secrets=True,
        comment_out_defaults=True,
    ).splitlines() == [
        "# For further information about options in this file see:",
        "#   https://docs.mopidy.com/",
        "#",
        "# The initial commented out values reflect the defaults as of:",
        f"#   mopidy {mopidy.__version__}",
        "#",
        "# Available options and defaults might have changed since then,",
        "# run `mopidy config` to see the current effective config and",
        "# `mopidy --version` to check the current version.",
        "",
        "[core]",
        "#cache_dir = $XDG_CACHE_DIR/mopidy",
        "#config_dir = $XDG_CONFIG_DIR/mopidy",
        "#data_dir = $XDG_DATA_DIR/mopidy",
        "#max_tracklist_length = 10000",
        "#restore_state = false",
        "",
        "[logging]",
        "#verbosity = 0",
        (
            "#format = "
            "[dim green]%(threadName)s[/dim green] "
            "[dim yellow]%(name)s[/dim yellow]\\n%(message)s"
        ),
        "#color = true",
        "#config_file = ",
        "",
        "[audio]",
        "#mixer = software",
        "#mixer_volume = ",
        "#output = autoaudiosink",
        "#buffer_time = ",
        "",
        "[proxy]",
        "#scheme = ",
        "#hostname = ",
        "#port = ",
        "#username = ",
        "#password = ",
    ]


def test_config_is_read_only():
    config_loader = ConfigLoader.only_defaults(extensions=None)
    config_manager = config_loader.validate()
    config = config_manager.config

    with pytest.raises(
        TypeError,
        match="'ConfigSection' object does not support item assignment",
    ):
        config["core"]["max_tracklist_length"] = 20000


def test_config_overrides():
    config_loader = ConfigLoader(
        paths=[],
        overrides={
            "core": {
                "max_tracklist_length": "5000",
                "restore_state": "true",
            },
        },
        extensions=ExtensionManager(),
    )
    config_manager = config_loader.validate()

    # core/max_tracklist_length defaults to 10000
    assert config_loader.raw_config["core"]["max_tracklist_length"] == "5000"
    assert config_manager.config["core"]["max_tracklist_length"] == 5000

    # core/restore_state defaults to false
    assert config_loader.raw_config["core"]["restore_state"] == "true"
    assert config_manager.config["core"]["restore_state"] is True


def test_config_errors():
    config_loader = ConfigLoader(
        paths=[],
        overrides={
            "core": {
                "max_tracklist_length": "not-an-integer",
            },
        },
        extensions=ExtensionManager(),
    )
    config_manager = config_loader.validate()

    # Raw config retains the invalid string
    assert config_loader.raw_config["core"]["max_tracklist_length"] == "not-an-integer"

    # Validation errors describes the problem
    assert "core" in config_manager.errors
    assert "max_tracklist_length" in config_manager.errors["core"]
    assert (
        config_manager.errors["core"]["max_tracklist_length"]
        == "invalid literal for int() with base 10: 'not-an-integer'"
    )

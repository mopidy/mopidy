import pytest

from mopidy.internal import log


@pytest.fixture
def config():
    return {
        "verbosity": 2,
        "format": "%(levelname)-8s %(message)s",
        "color": True,
        "config_file": None,
    }


def test_get_verbosity_level_args(config):
    assert log.get_verbosity_level(config, 2, 1) == 3


def test_get_verbosity_level_args_negative(config):
    assert log.get_verbosity_level(config, 3, -1) == 2


def test_get_verbosity_level_config(config):
    assert log.get_verbosity_level(config, 2, 0) == 4


def test_get_verbosity_level_config_none(config):
    config["verbosity"] = None
    assert log.get_verbosity_level(config, 2, 0) == 2


def test_get_verbosity_level_min(config):
    level = log.get_verbosity_level(config, 1, -9)
    assert log.LOG_LEVELS[level]


def test_get_verbosity_level_max(config):
    level = log.get_verbosity_level(config, 1, 9)
    assert log.LOG_LEVELS[level]

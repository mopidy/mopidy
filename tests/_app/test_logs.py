from mopidy._app.logs import LOG_LEVELS, get_verbosity_level


def test_get_verbosity_level_from_cli():
    assert get_verbosity_level(config_value=2, cli_value=1) == 1


def test_get_verbosity_level_from_cli_negative():
    assert get_verbosity_level(config_value=2, cli_value=-1) == -1


def test_get_verbosity_level_from_config():
    assert get_verbosity_level(config_value=2, cli_value=0) == 2


def test_get_verbosity_level_from_config_none():
    assert get_verbosity_level(config_value=None, cli_value=2) == 2


def test_get_verbosity_level_min():
    level = get_verbosity_level(config_value=0, cli_value=-9)
    assert level == min(LOG_LEVELS.keys())


def test_get_verbosity_level_max():
    level = get_verbosity_level(config_value=0, cli_value=9)
    assert level == max(LOG_LEVELS.keys())

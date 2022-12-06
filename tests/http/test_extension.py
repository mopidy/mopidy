from mopidy import config as config_lib
from mopidy.http import Extension


def test_get_default_config():
    ext = Extension()

    config = ext.get_default_config()

    assert "[http]" in config
    assert "enabled = true" in config


def test_get_config_schema():
    ext = Extension()

    schema = ext.get_config_schema()

    assert "enabled" in schema
    assert "hostname" in schema
    assert "port" in schema
    assert "zeroconf" in schema
    assert "allowed_origins" in schema
    assert "csrf_protection" in schema
    assert "default_app" in schema


def test_default_config_is_valid():
    ext = Extension()

    config = ext.get_default_config()
    schema = ext.get_config_schema()
    _, errors = config_lib.load([], [schema], [config], [])

    assert errors.get("http") is None

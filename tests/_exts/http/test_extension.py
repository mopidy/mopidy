from mopidy._exts.http import Extension


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

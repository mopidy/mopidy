from mopidy._app import server


def test_config_overrides():
    cmd = server.ServerCommand()
    result = cmd.parse(["--option", "foo/bar=baz"])

    assert result.config_overrides[0] == ("foo", "bar", "baz")

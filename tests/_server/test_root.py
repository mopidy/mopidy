from mopidy._server import root


def test_config_overrides():
    cmd = root.RootCommand()
    result = cmd.parse(["--option", "foo/bar=baz"])

    assert result.config_overrides[0] == ("foo", "bar", "baz")

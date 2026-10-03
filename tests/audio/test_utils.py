from mopidy.audio import supported_uri_schemes
from mopidy.types import UriScheme


def test_supported_uri_schemes_keeps_the_schemes_gstreamer_handles():
    result = supported_uri_schemes([UriScheme("file")])

    assert result == {UriScheme("file")}


def test_supported_uri_schemes_drops_the_schemes_it_does_not_handle():
    result = supported_uri_schemes([UriScheme("no-such-scheme")])

    assert result == set()


def test_supported_uri_schemes_keeps_only_the_handled_schemes_from_a_mix():
    result = supported_uri_schemes([UriScheme("file"), UriScheme("no-such-scheme")])

    assert result == {UriScheme("file")}

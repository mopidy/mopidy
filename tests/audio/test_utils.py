from mopidy._lib.gi import Gst
from mopidy.audio import supported_uri_schemes
from mopidy.audio._utils import setup_proxy
from mopidy.types import UriScheme

PROXY_CONFIG = {
    "scheme": "https",
    "hostname": "proxy.example.com",
    "port": 3128,
    "username": "alice",
    "password": "s3cret",
}


def test_supported_uri_schemes_keeps_the_schemes_gstreamer_handles():
    result = supported_uri_schemes([UriScheme("file")])

    assert result == {UriScheme("file")}


def test_supported_uri_schemes_drops_the_schemes_it_does_not_handle():
    result = supported_uri_schemes([UriScheme("no-such-scheme")])

    assert result == set()


def test_supported_uri_schemes_filters_rather_than_lists_everything():
    result = supported_uri_schemes([UriScheme("file"), UriScheme("no-such-scheme")])

    assert result == {UriScheme("file")}


def test_setup_proxy_sets_the_proxy_properties():
    element = Gst.ElementFactory.make("souphttpsrc")
    assert element is not None

    setup_proxy(element, PROXY_CONFIG)

    # souphttpsrc normalises the value it is given into a URI.
    assert element.get_property("proxy") == "https://proxy.example.com:3128/"
    assert element.get_property("proxy-id") == "alice"
    assert element.get_property("proxy-pw") == "s3cret"


def test_setup_proxy_leaves_the_element_alone_without_a_hostname():
    element = Gst.ElementFactory.make("souphttpsrc")
    assert element is not None

    setup_proxy(element, {"scheme": "https", "port": 3128})

    assert element.get_property("proxy") == ""


def test_setup_proxy_ignores_elements_with_no_proxy_property():
    element = Gst.ElementFactory.make("filesrc")
    assert element is not None

    setup_proxy(element, PROXY_CONFIG)

    assert not hasattr(element.props, "proxy")

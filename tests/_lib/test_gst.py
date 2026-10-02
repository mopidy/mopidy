from mopidy._lib.gi import GLib, GObject, Gst
from mopidy._lib.gst import convert_taglist, repr_tags, setup_proxy

PROXY_CONFIG = {
    "scheme": "https",
    "hostname": "proxy.example.com",
    "port": 3128,
    "username": "alice",
    "password": "s3cret",
}


def test_setup_proxy_sets_the_proxy_properties():
    element = Gst.ElementFactory.make("souphttpsrc")
    assert element is not None

    setup_proxy(element, PROXY_CONFIG)

    # souphttpsrc normalizes the value it is given into a URI.
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


def test_repr_tags_bytes_truncated_default():
    taglist = {"foo": [b"abcdefghijkl", b"mnop", "qrstuvwxyzabc"]}

    result = repr_tags(taglist)

    assert result == "{'foo': [b'abcdefghij...', b'mnop', 'qrstuvwxyzabc']}"


def test_repr_tags_max_bytes_two():
    taglist = {"foo": [b"1234", b"5678", "abcd", 67]}

    result = repr_tags(taglist, 2)

    assert result == "{'foo': [b'12...', b'56...', 'abcd', 67]}"


def make_taglist(tag, values):
    taglist = Gst.TagList.new_empty()

    for value in values:
        if isinstance(value, GLib.Date | Gst.DateTime):
            taglist.add_value(Gst.TagMergeMode.APPEND, tag, value)
            continue

        gobject_value = GObject.Value()
        if isinstance(value, bytes):
            gobject_value.init(GObject.TYPE_STRING)
            gobject_value.set_string(value.decode())
        elif isinstance(value, str):
            gobject_value.init(GObject.TYPE_STRING)
            gobject_value.set_string(value)
        elif isinstance(value, int):
            gobject_value.init(GObject.TYPE_UINT)
            gobject_value.set_uint(value)
        else:
            raise TypeError
        taglist.add_value(Gst.TagMergeMode.APPEND, tag, gobject_value)

    return taglist


def test_convert_taglist_date_tag():
    date = GLib.Date.new_dmy(7, 1, 2014)
    taglist = make_taglist(Gst.TAG_DATE, [date])

    result = convert_taglist(taglist)

    assert isinstance(result[Gst.TAG_DATE][0], str)
    assert result[Gst.TAG_DATE][0] == "2014-01-07"


def test_convert_taglist_date_tag_bad_value():
    date = GLib.Date.new_dmy(7, 1, 10000)
    taglist = make_taglist(Gst.TAG_DATE, [date])

    result = convert_taglist(taglist)

    assert len(result[Gst.TAG_DATE]) == 0


def test_convert_taglist_date_time_tag():
    taglist = make_taglist(
        Gst.TAG_DATE_TIME,
        [Gst.DateTime.new_from_iso8601_string("2014-01-07 14:13:12")],
    )

    result = convert_taglist(taglist)

    assert isinstance(result[Gst.TAG_DATE_TIME][0], str)
    assert result[Gst.TAG_DATE_TIME][0] == "2014-01-07T14:13:12Z"


def test_convert_taglist_date_time_tag_partial():
    # GStreamer emits partial dates when the tag only has a year, or a year
    # and a month. Both must be accepted by the `date` field on our models.
    taglist = make_taglist(
        Gst.TAG_DATE_TIME,
        [Gst.DateTime.new_y(2014)],
    )
    assert convert_taglist(taglist)[Gst.TAG_DATE_TIME] == ["2014"]

    taglist = make_taglist(
        Gst.TAG_DATE_TIME,
        [Gst.DateTime.new_ym(2014, 1)],
    )
    assert convert_taglist(taglist)[Gst.TAG_DATE_TIME] == ["2014-01"]


def test_convert_taglist_string_tag():
    taglist = make_taglist(Gst.TAG_ARTIST, [b"ABBA", b"ACDC"])

    result = convert_taglist(taglist)

    assert isinstance(result[Gst.TAG_ARTIST][0], str)
    assert result[Gst.TAG_ARTIST][0] == "ABBA"
    assert isinstance(result[Gst.TAG_ARTIST][1], str)
    assert result[Gst.TAG_ARTIST][1] == "ACDC"


def test_convert_taglist_sample_tag():
    # Image tags carry a Gst.Sample, which is unwrapped to the raw bytes.
    buf = Gst.Buffer.new_wrapped(b"fake image data")
    value = GObject.Value()
    value.init(Gst.Sample.__gtype__)
    value.set_boxed(Gst.Sample.new(buf, None, None, None))
    taglist = Gst.TagList.new_empty()
    taglist.add_value(Gst.TagMergeMode.APPEND, "image", value)

    result = convert_taglist(taglist)

    assert result["image"] == [b"fake image data"]


def test_convert_taglist_integer_tag():
    taglist = make_taglist(Gst.TAG_BITRATE, [17])

    result = convert_taglist(taglist)

    assert result[Gst.TAG_BITRATE][0] == 17

import pygst
pygst.require('0.10')
import gst

from mopidy import settings


def custom():
    """
    Custom output for using alternate setups.

    This output is intended to handle two main cases:

    1. Simple things like switching which sink to use. Say :class:`LocalOutput`
       doesn't work for you and you want to switch to ALSA, simple. Set
       :attr:`mopidy.settings.CUSTOM_OUTPUT` to ``alsasink`` and you are good
       to go. Some possible sinks include:

       - alsasink
       - osssink
       - pulsesink
       - ...and many more

    2. Advanced setups that require complete control of the output bin. For
       these cases setup :attr:`mopidy.settings.CUSTOM_OUTPUT` with a
       :command:`gst-launch` compatible string describing the target setup.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.CUSTOM_OUTPUT`
    """
    return gst.parse_bin_from_description(settings.CUSTOM_OUTPUT, True)


def local():
    """
    Basic output to local audio sink.

    This output will normally tell GStreamer to choose whatever it thinks is
    best for your system. In other words this is usually a sane choice.

    **Dependencies:**

    - None

    **Settings:**

    - None
    """
    return  gst.parse_bin_from_description('autoaudiosink', True)


def shoutcast():
    """
    Shoutcast streaming output.

    This output allows for streaming to an icecast server or anything else that
    supports Shoutcast. The output supports setting for: server address, port,
    mount point, user, password and encoder to use. Please see
    :class:`mopidy.settings` for details about settings.

    **Dependencies:**

    - A SHOUTcast/Icecast server

    **Settings:**

    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_HOSTNAME`
    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_PORT`
    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_USERNAME`
    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_PASSWORD`
    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_MOUNT`
    - :attr:`mopidy.settings.SHOUTCAST_OUTPUT_ENCODER`
    """
    encoder = settings.SHOUTCAST_OUTPUT_ENCODER
    output = gst.parse_bin_from_description(
        '%s ! shout2send name=shoutcast' % encoder, True)

    shoutcast = output.get_by_name('shoutcast')

    properties = {
        u'ip': settings.SHOUTCAST_OUTPUT_HOSTNAME,
        u'port': settings.SHOUTCAST_OUTPUT_PORT,
        u'mount': settings.SHOUTCAST_OUTPUT_MOUNT,
        u'username': settings.SHOUTCAST_OUTPUT_USERNAME,
        u'password': settings.SHOUTCAST_OUTPUT_PASSWORD,
    }

    for name, value in properties.items():
        shoutcast.set_property(name, value)

    return output

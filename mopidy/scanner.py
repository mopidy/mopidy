import gobject
gobject.threads_init()

import pygst
pygst.require('0.10')
import gst
import sys

def main(uri):
    pipeline = gst.element_factory_make('playbin2')

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect('message::tag', process_gst_message)

    pipeline.set_property('uri', uri)
    pipeline.set_state(gst.STATE_PAUSED)

    gobject.MainLoop().run()

def process_gst_message(bus, message):
    data = message.parse_tag()
    tags = dict([(k, data[k]) for k in data.keys()])

    print tags

if __name__ == '__main__':
    main(sys.argv[1])

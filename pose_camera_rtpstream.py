import sys
import traceback
import argparse

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
gi.require_version('GObject', '2.0')
from gi.repository import Gst, GObject, GstApp  # noqa:F401,F402

# Initializes Gstreamer, it's variables, paths
Gst.init(sys.argv)

DEFAULT_PIPELINE = "v4l2src device=/dev/video0 " \
                   "! video/x-raw,width=640,height=480 " \
                   "! videoconvert name=videoconvert_elem " \
                   "! x264enc " \
                   "! rtph264pay config-interval=1 pt=96 " \
                   "! udpsink host=192.168.3.255 auto-multicast=true port=5000"


def on_message(bus: Gst.Bus, message: Gst.Message, loop: GObject.MainLoop):
    mtype = message.type

    if mtype == Gst.MessageType.EOS:
        print("End of stream")
        loop.quit()

    elif mtype == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(err, debug)
        loop.quit()

    elif mtype == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(err, debug)

    return True

pipeline = Gst.parse_launch(DEFAULT_PIPELINE)

# trying to get an excess to the videoconvert sink pad
videoconvert_elem = pipeline.get_by_name("videoconvert_elem")
videoconvert_sink_pad = videoconvert_elem.get_static_pad("sink")

def padProbeCallBack(pad, info, pdata):
    buffer = info.get_buffer()
    #Gst.MiniObject.set_writable(buffer.mini_object)
    #print('hey')
    #print(type(buffer.mini_object), ">>>", buffer.is_all_memory_writable())
    # print(type(info.id) + ">>>" + info.id)
    # print(type(info.offset) + ">>>" + info.offset)
    # print(type(info.size) + ">>>" + info.size)
    # print(type(info.type) + ">>>" + info.type)
    print('\n\n')
    return Gst.PadProbeReturn.OK

pdata = {pipeline, videoconvert_elem}
videoconvert_sink_pad.add_probe(Gst.PadProbeType.BUFFER, padProbeCallBack, pdata)


# end of trying

bus = pipeline.get_bus()
bus.add_signal_watch()
pipeline.set_state(Gst.State.PLAYING)
loop = GObject.MainLoop()
bus.connect("message", on_message, loop)

try:
    loop.run()
except Exception:
    traceback.print_exc()
    loop.quit()

# Stop Pipeline
pipeline.set_state(Gst.State.NULL)
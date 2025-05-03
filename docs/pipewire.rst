.. _pipewire:

********
PipeWire
********

In order to configure mopidy to work with PipeWire, you need to also have pipewire-pulse
and run pipewire-pulse as a tcp server, typically in addition to running it via socket.

That is accomplished by setting the following in its configuration. The location depends on your distribution, in Arch Linux it's located at `/usr/share/pipewire/pipewire-pulse.conf`.
    
    pulse.properties = {
        # the addresses this server listens on
        server.address = [
            "unix:native"
            "tcp:4713"
        ]
    }

After that is set, configure mopidy to use the pipewire-pulse server (the ports on both configurations must match), in mopidy's config:

    [audio]
    output = pulsesink server=127.0.0.1:4713

Restart the pipewire-pulse service mopidy, this should be enough to get it working.

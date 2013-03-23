*********************
Extension development
*********************

.. warning:: Draft

    This document is a draft open for discussion. It shows how we imagine that
    development of Mopidy extensions should become in the future, not how to
    currently develop an extension for Mopidy.

An extension wants to:

- Be automatically found if installed
- Provide default config
- Validate configuration
- Validate presence of dependencies
  - Python packages (e.g. pyspotify)
  - Other software
  - Other extensions (e.g. SoundCloud depends on stream backend)
- Validate that needed TCP ports are free
- Be asked to start running
- Be asked to shut down

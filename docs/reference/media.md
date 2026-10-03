# Media API

The media API reads media without playing it. Use it to get the metadata of a
URI as a [Track][mopidy.models.Track].

Make one reader when your backend starts, and close it when your backend stops:

```python
import pykka

from mopidy import backend
from mopidy.media import Reader
from mopidy.types import DurationMs


class MyBackend(pykka.ThreadingActor, backend.Backend):
    def __init__(self, *, config, audio):
        super().__init__(config=config, audio=audio)
        self.media_reader = Reader.create(config=config, timeout=DurationMs(5000))

    def on_stop(self) -> None:
        self.media_reader.close()
```

::: mopidy.media
    options:
      heading_level: 2

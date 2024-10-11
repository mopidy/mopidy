import json
from typing import Any

import msgspec

from mopidy.models._base import BaseModel, ModelRegistry


class ModelJSONEncoder(json.JSONEncoder):
    """Automatically serialize Mopidy models to JSON.

    Usage::

        >>> import json
        >>> json.dumps(
        ...     {'a_track': Track(name='name')},
        ...     cls=ModelJSONEncoder,
        ... )
        '{"a_track": {"__model__": "Track", "name": "name"}}'

    """

    def default(self, o) -> Any:
        if isinstance(o, BaseModel):
            return o.serialize()
        return json.JSONEncoder.default(self, o)


def model_json_decoder(dct) -> Any:
    """Automatically deserialize Mopidy models from JSON.

    Usage::

        >>> import json
        >>> json.loads(
        ...     '{"a_track": {"__model__": "Track", "name": "name"}}',
        ...     object_hook=model_json_decoder,
        ... )
        {u'a_track': Track(artists=[], name=u'name')}

    """
    if model_name := dct.get("__model__"):
        model = ModelRegistry.get(model_name)
        return msgspec.convert(dct, type=model)
    return dct

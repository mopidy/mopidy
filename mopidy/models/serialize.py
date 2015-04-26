from __future__ import absolute_import, unicode_literals

import json

from mopidy.models.immutable import ImmutableObject


class ModelJSONEncoder(json.JSONEncoder):

    """
    Automatically serialize Mopidy models to JSON.

    Usage::

        >>> import json
        >>> json.dumps({'a_track': Track(name='name')}, cls=ModelJSONEncoder)
        '{"a_track": {"__model__": "Track", "name": "name"}}'

    """

    def default(self, obj):
        if isinstance(obj, ImmutableObject):
            return obj.serialize()
        return json.JSONEncoder.default(self, obj)


def model_json_decoder(dct):
    """
    Automatically deserialize Mopidy models from JSON.

    Usage::

        >>> import json
        >>> json.loads(
        ...     '{"a_track": {"__model__": "Track", "name": "name"}}',
        ...     object_hook=model_json_decoder)
        {u'a_track': Track(artists=[], name=u'name')}

    """
    if '__model__' in dct:
        models = {c.__name__: c for c in ImmutableObject.__subclasses__()}
        model_name = dct.pop('__model__')
        if model_name in models:
            return models[model_name](**dct)
    return dct

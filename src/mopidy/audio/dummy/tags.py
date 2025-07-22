import warnings

from mopidy.models import Track


def convert_tags_to_track(_tags: dict) -> Track:
    warnings.warn("This is a dummy implementation", stacklevel=2)
    return Track()

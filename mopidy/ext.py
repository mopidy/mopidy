from __future__ import unicode_literals


class Extension(object):

    name = None
    version = None

    def get_default_config(self):
        raise NotImplementedError(
            'Add at least a config section with "enabled = true"')

    def validate_config(self, config):
        raise NotImplementedError(
            'You must explicitly pass config validation if not needed')

    def validate_environment(self):
        pass

    def get_frontend_classes(self):
        return []

    def get_backend_classes(self):
        return []

    def register_gstreamer_elements(self):
        pass

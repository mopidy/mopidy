from __future__ import unicode_literals

from mopidy.utils import config


class Extension(object):

    name = None
    version = None

    def get_default_config(self):
        raise NotImplementedError(
            'Add at least a config section with "enabled = true"')

    def get_config_schema(self):
        return config.ExtensionConfigSchema()

    def validate_environment(self):
        pass

    def get_frontend_classes(self):
        return []

    def get_backend_classes(self):
        return []

    def register_gstreamer_elements(self):
        pass

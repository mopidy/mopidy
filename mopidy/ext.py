from __future__ import unicode_literals

from mopidy.utils import config


class Extension(object):

    dist_name = None
    name = None
    version = None

    @property
    def ext_name(self):
        if self.name is None:
            return None
        return 'ext.%s' % self.name

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

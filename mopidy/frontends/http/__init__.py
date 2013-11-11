from __future__ import unicode_literals

import os

import mopidy
from mopidy import config, exceptions, ext


class Extension(ext.Extension):

    dist_name = 'Mopidy-HTTP'
    ext_name = 'http'
    version = mopidy.__version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['hostname'] = config.Hostname()
        schema['port'] = config.Port()
        schema['static_dir'] = config.Path(optional=True)
        schema['zeroconf'] = config.String(optional=True)
        return schema

    def validate_environment(self):
        try:
            import cherrypy  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('cherrypy library not found', e)

        try:
            import ws4py  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('ws4py library not found', e)

    def get_frontend_classes(self):
        from .actor import HttpFrontend
        return [HttpFrontend]

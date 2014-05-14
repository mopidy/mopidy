from __future__ import unicode_literals

import logging
import os

import tornado.web

from mopidy import __version__, config as config_lib, exceptions, ext


logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = 'Mopidy-HTTP'
    ext_name = 'http'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config_lib.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        schema['hostname'] = config_lib.Hostname()
        schema['port'] = config_lib.Port()
        schema['static_dir'] = config_lib.Path(optional=True)
        schema['zeroconf'] = config_lib.String(optional=True)
        return schema

    def validate_environment(self):
        try:
            import tornado.web  # noqa
        except ImportError as e:
            raise exceptions.ExtensionError('tornado library not found', e)

    def setup(self, registry):
        from .actor import HttpFrontend

        HttpFrontend.routers = registry['http:routers']
        registry.add('frontend', HttpFrontend)


class StaticFileHandler(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-Control", "no-cache")
        self.set_header("X-Mopidy-Version", __version__.encode('utf-8'))


class Router(object):
    """
    HTTP router interface.

    Extensions that wish to add custom routes to HTTP server
    need to sub-class this class and install and configure it with an
    extension.

    :param config:dict Config dictionary
    """

    #: Name of the HTTP router implementation, must be overridden.
    name = None

    #: Path to location of static files.
    path = None

    def __init__(self, config):
        self.config = config
        self.hostname = config['http']['hostname']
        self.port = config['http']['port']
        if not self.name:
            raise ValueError('Undefined name in %s' % self)

    def linkify(self):
        """
        Absolute URL to the root of this router.

        :return string: URI
        """
        return 'http://%s:%s/%s/' % (self.hostname, self.port, self.name)

    def setup_routes(self):
        """
        Configure routes for this interface

        Implementation must return list of routes, compatible with
        :`class:tornado.web.Application`.

        :return list: List of tornado routes
        """

        if not self.path:
            raise ValueError('Undefined path in %s' % self)
        logger.info(
            'Serving HTTP extension %s at %s' %
            (type(self), self.linkify())
        )
        return [
            (r"/%s/(.*)" % self.name, StaticFileHandler, {
                'path': self.path,
                'default_filename': 'index.html'
            })
        ]

from __future__ import unicode_literals

import logging
import os

import mopidy
from mopidy import config as config_lib, exceptions, ext


logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name = 'Mopidy-HTTP'
    ext_name = 'http'
    version = mopidy.__version__

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
        from .handlers import mopidy_app_factory

        HttpFrontend.apps = registry['http:app']
        HttpFrontend.statics = registry['http:static']

        registry.add('frontend', HttpFrontend)
        registry.add('http:app', {
            'name': 'mopidy',
            'factory': mopidy_app_factory,
        })


class Router(object):
    """
    HTTP router interface.

    Extensions that wish to extend the HTTP server needs to subclass this class
    and have :meth:`~mopidy.ext.Extension.setup` register the class in the
    extension registry under the ``http:router`` key.

    :param config: dict structure of the entire Mopidy configuration
    :param core: :class:`pykka.ActorProxy` to the core actor, giving full
      access to the core API
    """

    name = None
    """Name of the HTTP router.

    Must be overridden by all subclasses.

    This should be the same as the :attr:`~mopidy.ext.Extension.ext_name` of
    the Mopidy extension implementing an HTTP router. The :attr:`~Router.name`
    will be used to namespace all URLs handled by this router.

    For example, if :attr:`~Router.name` is ``soundspot``, then the router will
    manage all requests starting with ``http://localhost:6680/soundspot``.
    """

    def __init__(self, config, core):
        self.config = config
        self.core = core
        if not self.name:
            raise ValueError('Router name must be set')

    def get_request_handlers(self):
        """
        Get request handlers for the URL namespace owned by this router.

        Must be overridden by all subclasses.

        Returns a list of request handlers compatible with
        :class:`tornado.web.Application`. The URL patterns should not include
        the :attr:`name` prefix, as that will be prepended by the web server.
        """
        raise NotImplementedError

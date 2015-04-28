from __future__ import unicode_literals


def format_proxy(proxy_config):
    """Convert a Mopidy proxy config to the commonly used proxy string format.

    Outputs ``scheme://host:port``, ``scheme://user:pass@host:port`` or
    :class:`None` depending on the proxy config provided.
    """
    if not proxy_config.get('hostname'):
        return None

    if proxy_config.get('username') and proxy_config.get('password'):
        template = '{scheme}://{username}:{password}@{hostname}:{port}'
    else:
        template = '{scheme}://{hostname}:{port}'

    port = proxy_config.get('port', 80)
    if port < 0:
        port = 80

    return template.format(scheme=proxy_config.get('scheme', 'http'),
                           username=proxy_config.get('username'),
                           password=proxy_config.get('password'),
                           hostname=proxy_config['hostname'], port=port)

import platform

import mopidy

"Helpers for configuring HTTP clients used in Mopidy extensions."


def format_proxy(proxy_config, auth=True):
    """Convert a Mopidy proxy config to the commonly used proxy string format.

    Outputs ``scheme://host:port``, ``scheme://user:pass@host:port`` or
    :class:`None` depending on the proxy config provided.

    You can also opt out of getting the basic auth by setting ``auth`` to
    :class:`False`.

    .. versionadded:: 1.1
    """
    if not proxy_config.get("hostname"):
        return None

    scheme = proxy_config.get("scheme") or "http"
    username = proxy_config.get("username")
    password = proxy_config.get("password")
    hostname = proxy_config["hostname"]
    port = proxy_config.get("port")
    if not port or port < 0:
        port = 80

    if username and password and auth:
        return f"{scheme}://{username}:{password}@{hostname}:{port}"
    else:
        return f"{scheme}://{hostname}:{port}"


def format_user_agent(name=None):
    """Construct a User-Agent suitable for use in client code.

    This will identify use by the provided ``name`` (which should be on the
    format ``dist_name/version``), Mopidy version and Python version.

    .. versionadded:: 1.1
    """
    parts = [
        f"Mopidy/{mopidy.__version__}",
        f"{platform.python_implementation()}/{platform.python_version()}",
    ]
    if name:
        parts.insert(0, name)
    return " ".join(parts)

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import requests

from mopidy import httpclient

if TYPE_CHECKING:
    from mopidy.httpclient import ProxyConfig

logger = logging.getLogger(__name__)


def get_requests_session(
    proxy_config: ProxyConfig,
    user_agent: str,
) -> requests.Session:
    session = requests.Session()

    if proxy := httpclient.format_proxy(proxy_config):
        session.proxies.update({"http": proxy, "https": proxy})

    full_user_agent = httpclient.format_user_agent(user_agent)
    session.headers.update({"user-agent": full_user_agent})

    return session


def download(session, uri, timeout=1.0, chunk_size=4096):
    try:
        response = session.get(uri, stream=True, timeout=timeout)
    except requests.exceptions.Timeout:
        logger.warning(
            "Download of %r failed due to connection timeout after %.3fs",
            uri,
            timeout,
        )
        return None
    except requests.exceptions.InvalidSchema:
        logger.warning("Download of %r failed due to unsupported schema", uri)
        return None
    except requests.exceptions.RequestException as exc:
        logger.warning("Download of %r failed: %s", uri, exc)
        logger.debug("Download exception details", exc_info=True)
        return None

    content = []
    deadline = time.time() + timeout
    for chunk in response.iter_content(chunk_size):
        content.append(chunk)
        if time.time() > deadline:
            logger.warning(
                "Download of %r failed due to download taking more than %.3fs",
                uri,
                timeout,
            )
            return None

    if not response.ok:
        logger.warning("Problem downloading %r: %s", uri, response.reason)
        return None

    return b"".join(content)

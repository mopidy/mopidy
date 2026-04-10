from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import httpx

from mopidy import httpclient

if TYPE_CHECKING:
    from mopidy.httpclient import ProxyConfig

logger = logging.getLogger(__name__)


def get_httpx_client(
    proxy_config: ProxyConfig,
    user_agent: str,
) -> httpx.Client:
    return httpx.Client(
        proxy=httpclient.format_proxy(proxy_config),
        headers={"user-agent": httpclient.format_user_agent(user_agent)},
        follow_redirects=True,
    )


def download(
    client: httpx.Client,
    uri: str,
    timeout: float = 1.0,
    chunk_size: int = 4096,
) -> bytes | None:
    try:
        with client.stream("GET", uri, timeout=timeout) as response:
            content = []
            deadline = time.time() + timeout
            for chunk in response.iter_bytes(chunk_size):
                content.append(chunk)
                if time.time() > deadline:
                    logger.warning(
                        "Download of %r failed due to download taking more than %.3fs",
                        uri,
                        timeout,
                    )
                    return None

            if not response.is_success:
                logger.warning(
                    "Problem downloading %r: %s", uri, response.reason_phrase
                )
                return None

            return b"".join(content)
    except httpx.TimeoutException:
        logger.warning(
            "Download of %r failed due to connection timeout after %.3fs",
            uri,
            timeout,
        )
        return None
    except httpx.UnsupportedProtocol:
        logger.warning("Download of %r failed due to unsupported schema", uri)
        return None
    except httpx.HTTPError as exc:
        logger.warning("Download of %r failed: %s", uri, exc)
        logger.debug("Download exception details", exc_info=True)
        return None

import logging
import re
import socket

logger = logging.getLogger(__name__)


def try_ipv6_socket() -> bool:
    """Determine if system really supports IPv6"""
    if not socket.has_ipv6:
        return False
    try:
        socket.socket(socket.AF_INET6).close()
    except OSError as exc:
        logger.debug(
            f"Platform supports IPv6, but socket creation failed, disabling: {exc}",
        )
        return False
    else:
        return True


#: Boolean value that indicates if creating an IPv6 socket will succeed.
has_ipv6 = try_ipv6_socket()


def format_hostname(hostname: str) -> str:
    """Format hostname for display."""
    if has_ipv6 and re.match(r"\d+.\d+.\d+.\d+", hostname) is not None:
        hostname = f"::ffff:{hostname}"
    return hostname

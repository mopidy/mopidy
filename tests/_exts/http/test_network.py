from pytest_mock import MockFixture

from mopidy._exts.http import network


def test_try_ipv6_socket_when_system_claims_no_ipv6_support(mocker: MockFixture):
    mocker.patch("socket.has_ipv6", False)

    assert not network.try_ipv6_socket()


def test_try_ipv6_socket_on_system_with_broken_ipv6(mocker: MockFixture):
    mocker.patch("socket.has_ipv6", True)
    mocker.patch("socket.socket", side_effect=OSError())

    assert not network.try_ipv6_socket()


def test_with_working_ipv6(mocker: MockFixture):
    mocker.patch("socket.has_ipv6", True)
    mocker.patch("socket.socket")

    assert network.try_ipv6_socket()


def test_format_hostname_prefixes_ipv4_addresses_when_ipv6_available(
    mocker: MockFixture,
):
    mocker.patch("mopidy._exts.http.network.has_ipv6", True)

    assert network.has_ipv6 is True
    assert network.format_hostname("0.0.0.0") == "::ffff:0.0.0.0"  # noqa: S104
    assert network.format_hostname("1.0.0.1") == "::ffff:1.0.0.1"


def test_format_hostname_does_nothing_when_only_ipv4_available(mocker: MockFixture):
    mocker.patch("mopidy._exts.http.network.has_ipv6", False)

    assert network.has_ipv6 is False
    assert network.format_hostname("0.0.0.0") == "0.0.0.0"  # noqa: S104

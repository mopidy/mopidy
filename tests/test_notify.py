from pytest_mock import MockerFixture

from mopidy.notify import Notifier


def test_info_sends_a_notification(mocker: MockerFixture) -> None:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    notifier.info("hello")
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="info"
    )


def test_warning_sends_a_notification(mocker: MockerFixture) -> None:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    notifier.warning("hello")
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="warning"
    )


def test_error_sends_a_notification(mocker: MockerFixture) -> None:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    notifier.error("hello")
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="error"
    )

from pytest_mock import MockerFixture

from mopidy.notify import Notifier


def test_info_sends_a_notification(mocker: MockerFixture) -> None:
    # Arrange:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    # Act:
    notifier.info("hello")
    # Assert:
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="info"
    )


def test_warning_sends_a_notification(mocker: MockerFixture) -> None:
    # Arrange:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    # Act:
    notifier.warning("hello")
    # Assert:
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="warning"
    )


def test_error_sends_a_notification(mocker: MockerFixture) -> None:
    # Arrange:
    notifier = Notifier("spotify")
    fake_send = mocker.patch("mopidy.notify.CoreListener.send")

    # Act:
    notifier.error("hello")
    # Assert:
    fake_send.assert_called_once_with(
        "notification", message="hello", source="spotify", level="error"
    )

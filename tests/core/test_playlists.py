from unittest import mock

import pytest

from mopidy.backend import PlaylistsProvider
from mopidy.core import Core, CoreListener, _playlists
from mopidy.models import Playlist, Ref, Track
from mopidy.types import Uri
from tests.factories import PlaylistFactory


@pytest.fixture
def plr1a():
    return Ref.playlist(
        uri=Uri("dummy1:pl:a"),
        name="A",
    )


@pytest.fixture
def plr1b():
    return Ref.playlist(
        uri=Uri("dummy1:pl:b"),
        name="B",
    )


@pytest.fixture
def plr2a():
    return Ref.playlist(
        uri=Uri("dummy2:pl:a"),
        name="A",
    )


@pytest.fixture
def plr2b():
    return Ref.playlist(
        uri=Uri("dummy2:pl:b"),
        name="B",
    )


@pytest.fixture
def pl1a():
    return Playlist(
        uri=Uri("dummy1:pl:a"),
        name="A",
        tracks=[Track(uri="dummy1:t:a")],
    )


@pytest.fixture
def pl1b():
    return Playlist(
        uri=Uri("dummy1:pl:b"),
        name="B",
        tracks=[Track(uri="dummy1:t:b")],
    )


@pytest.fixture
def pl2a():
    return Playlist(
        uri=Uri("dummy2:pl:a"),
        name="A",
        tracks=[Track(uri="dummy2:t:a")],
    )


@pytest.fixture
def pl2b():
    return Playlist(
        uri=Uri("dummy2:pl:b"),
        name="B",
        tracks=[Track(uri="dummy2:t:b")],
    )


@pytest.fixture
def sp1(plr1a, plr1b, pl1a, pl1b):
    sp1 = mock.Mock(spec=PlaylistsProvider)
    sp1.as_list.return_value.get.return_value = [
        plr1a,
        plr1b,
    ]
    sp1.lookup.return_value.get.side_effect = [pl1a, pl1b]
    return sp1


@pytest.fixture
def sp2(plr2a, plr2b, pl2a, pl2b):
    sp2 = mock.Mock(spec=PlaylistsProvider)
    sp2.as_list.return_value.get.return_value = [
        plr2a,
        plr2b,
    ]
    sp2.lookup.return_value.get.side_effect = [pl2a, pl2b]
    return sp2


@pytest.fixture
def backend1(sp1):
    backend1 = mock.Mock()
    backend1.actor_ref.actor_class.__name__ = "Backend1"
    backend1.uri_schemes.get.return_value = ["dummy1"]
    backend1.playlists = sp1
    return backend1


@pytest.fixture
def backend2(sp2):
    backend2 = mock.Mock()
    backend2.actor_ref.actor_class.__name__ = "Backend2"
    backend2.uri_schemes.get.return_value = ["dummy2"]
    backend2.playlists = sp2
    return backend2


@pytest.fixture
def backend3():
    # A backend without the optional playlists provider
    backend3 = mock.Mock()
    backend3.uri_schemes.get.return_value = ["dummy3"]
    backend3.has_playlists().get.return_value = False
    backend3.playlists = None
    return backend3


@pytest.fixture
def core(backend1, backend2, backend3):
    return Core(
        config={},
        mixer=None,
        backends=[backend3, backend1, backend2],
    )


def test_as_list_combines_result_from_backends(core, plr1a, plr1b, plr2a, plr2b):
    result = core.playlists.as_list()

    assert plr1a in result
    assert plr1b in result
    assert plr2a in result
    assert plr2b in result


def test_as_list_ignores_backends_that_dont_support_it(core, sp2, plr1a, plr1b):
    sp2.as_list.return_value.get.side_effect = NotImplementedError

    result = core.playlists.as_list()

    assert len(result) == 2
    assert plr1a in result
    assert plr1b in result


def test_get_items_selects_the_matching_backend(core, sp1, sp2):
    ref = Ref.track(uri="uri", name="Foo")
    sp2.get_items.return_value.get.return_value = [ref]

    result = core.playlists.get_items("dummy2:pl:a")

    assert [ref] == result
    assert not sp1.get_items.called
    sp2.get_items.assert_called_once_with("dummy2:pl:a")


def test_get_items_with_unknown_uri_scheme_does_nothing(core, sp1, sp2):
    result = core.playlists.get_items("unknown:a")

    assert result is None
    assert not sp1.delete.called
    assert not sp2.delete.called


def test_create_without_uri_scheme_uses_first_backend(core, sp1, sp2):
    playlist = PlaylistFactory.build()
    sp1.create.return_value.get.return_value = playlist

    result = core.playlists.create("foo")

    assert playlist == result
    sp1.create.assert_called_once_with("foo")
    assert not sp2.create.called


def test_create_without_uri_scheme_ignores_none_result(core, sp1, sp2):
    playlist = PlaylistFactory.build()
    sp1.create.return_value.get.return_value = None
    sp2.create.return_value.get.return_value = playlist

    result = core.playlists.create("foo")

    assert playlist == result
    sp1.create.assert_called_once_with("foo")
    sp2.create.assert_called_once_with("foo")


def test_create_without_uri_scheme_ignores_exception(core, sp1, sp2):
    playlist = PlaylistFactory.build()
    sp1.create.return_value.get.side_effect = Exception
    sp2.create.return_value.get.return_value = playlist

    result = core.playlists.create("foo")

    assert playlist == result
    sp1.create.assert_called_once_with("foo")
    sp2.create.assert_called_once_with("foo")


def test_create_with_uri_scheme_selects_the_matching_backend(core, sp1, sp2):
    playlist = PlaylistFactory.build()
    sp2.create.return_value.get.return_value = playlist

    result = core.playlists.create("foo", uri_scheme="dummy2")

    assert playlist == result
    assert not sp1.create.called
    sp2.create.assert_called_once_with("foo")


def test_create_with_unsupported_uri_scheme_uses_first_backend(core, sp1, sp2):
    playlist = PlaylistFactory.build()
    sp1.create.return_value.get.return_value = playlist

    result = core.playlists.create("foo", uri_scheme="dummy3")

    assert playlist == result
    sp1.create.assert_called_once_with("foo")
    assert not sp2.create.called


def test_delete_selects_the_dummy1_backend(core, sp1, sp2):
    success = core.playlists.delete("dummy1:a")

    assert success
    sp1.delete.assert_called_once_with("dummy1:a")
    assert not sp2.delete.called


def test_delete_selects_the_dummy2_backend(core, sp1, sp2):
    success = core.playlists.delete("dummy2:a")

    assert success
    assert not sp1.delete.called
    sp2.delete.assert_called_once_with("dummy2:a")


def test_delete_with_unknown_uri_scheme_does_nothing(core, sp1, sp2):
    success = core.playlists.delete("unknown:a")

    assert not success
    assert not sp1.delete.called
    assert not sp2.delete.called


def test_delete_ignores_backend_without_playlist_support(core, sp1, sp2):
    success = core.playlists.delete("dummy3:a")

    assert not success
    assert not sp1.delete.called
    assert not sp2.delete.called


def test_lookup_selects_the_dummy1_backend(core, sp1, sp2):
    core.playlists.lookup("dummy1:a")

    sp1.lookup.assert_called_once_with("dummy1:a")
    assert not sp2.lookup.called


def test_lookup_selects_the_dummy2_backend(core, sp1, sp2):
    core.playlists.lookup("dummy2:a")

    assert not sp1.lookup.called
    sp2.lookup.assert_called_once_with("dummy2:a")


def test_lookup_track_in_backend_without_playlists_fails(core, sp1, sp2):
    result = core.playlists.lookup("dummy3:a")

    assert result is None
    assert not sp1.lookup.called
    assert not sp2.lookup.called


def test_refresh_without_uri_scheme_refreshes_all_backends(core, sp1, sp2):
    core.playlists.refresh()

    sp1.refresh.assert_called_once_with()
    sp2.refresh.assert_called_once_with()


def test_refresh_with_uri_scheme_refreshes_matching_backend(core, sp1, sp2):
    core.playlists.refresh(uri_scheme="dummy2")

    assert not sp1.refresh.called
    sp2.refresh.assert_called_once_with()


def test_refresh_with_unknown_uri_scheme_refreshes_nothing(core, sp1, sp2):
    core.playlists.refresh(uri_scheme="foobar")

    assert not sp1.refresh.called
    assert not sp2.refresh.called


def test_refresh_ignores_backend_without_playlist_support(core, sp1, sp2):
    core.playlists.refresh(uri_scheme="dummy3")

    assert not sp1.refresh.called
    assert not sp2.refresh.called


def test_save_selects_the_dummy1_backend(core, sp1, sp2):
    playlist = Playlist(uri="dummy1:a")
    sp1.save.return_value.get.return_value = playlist

    result = core.playlists.save(playlist)

    assert playlist == result
    sp1.save.assert_called_once_with(playlist)
    assert not sp2.save.called


def test_save_selects_the_dummy2_backend(core, sp1, sp2):
    playlist = PlaylistFactory.build(uri="dummy2:a")
    sp2.save.return_value.get.return_value = playlist

    result = core.playlists.save(playlist)

    assert playlist == result
    assert not sp1.save.called
    sp2.save.assert_called_once_with(playlist)


def test_save_does_nothing_if_playlist_uri_is_unset(core, sp1, sp2):
    result = core.playlists.save(PlaylistFactory.build())

    assert result is None
    assert not sp1.save.called
    assert not sp2.save.called


def test_save_does_nothing_if_playlist_uri_has_unknown_scheme(core, sp1, sp2):
    result = core.playlists.save(PlaylistFactory.build(uri="foobar:a"))

    assert result is None
    assert not sp1.save.called
    assert not sp2.save.called


def test_save_ignores_backend_without_playlist_support(core, sp1, sp2):
    result = core.playlists.save(PlaylistFactory.build(uri="dummy3:a"))

    assert result is None
    assert not sp1.save.called
    assert not sp2.save.called


def test_get_uri_schemes(core):
    result = core.playlists.get_uri_schemes()
    assert result == ["dummy1", "dummy2"]


@pytest.fixture
def playlists():
    return mock.Mock(spec=PlaylistsProvider)


@pytest.fixture
def backend(playlists):
    backend = mock.Mock()
    backend.actor_ref.actor_class.__name__ = "DummyBackend"
    backend.uri_schemes.get.return_value = ["dummy"]
    backend.playlists = playlists
    return backend


@pytest.fixture
def mock_backend_core(backend):
    return Core(
        config={},
        mixer=None,
        backends=[backend],
    )


@pytest.fixture
def logger(mocker):
    return mocker.patch.object(_playlists, "logger")


def test_as_list_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlists.as_list.return_value.get.side_effect = Exception
    assert mock_backend_core.playlists.as_list() == []
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_as_list_bad_backends_backend_returns_none(
    mock_backend_core, playlists, logger
):
    playlists.as_list.return_value.get.return_value = None
    assert mock_backend_core.playlists.as_list() == []
    assert not logger.error.called


def test_as_list_bad_backends_backend_returns_wrong_type(
    mock_backend_core, playlists, logger
):
    playlists.as_list.return_value.get.return_value = "abc"
    assert mock_backend_core.playlists.as_list() == []
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_items_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlists.get_items.return_value.get.side_effect = Exception
    assert mock_backend_core.playlists.get_items("dummy:/1") is None
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_get_items_bad_backends_backend_returns_none(
    mock_backend_core, playlists, logger
):
    playlists.get_items.return_value.get.return_value = None
    assert mock_backend_core.playlists.get_items("dummy:/1") is None
    assert not logger.error.called


def test_get_items_bad_backends_backend_returns_wrong_type(
    mock_backend_core, playlists, logger
):
    playlists.get_items.return_value.get.return_value = "abc"
    assert mock_backend_core.playlists.get_items("dummy:/1") is None
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_create_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlists.create.return_value.get.side_effect = Exception
    assert mock_backend_core.playlists.create("foobar") is None
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_create_bad_backends_backend_returns_none(mock_backend_core, playlists, logger):
    playlists.create.return_value.get.return_value = None
    assert mock_backend_core.playlists.create("foobar") is None
    assert not logger.error.called


def test_create_bad_backends_backend_returns_wrong_type(
    mock_backend_core, playlists, logger
):
    playlists.create.return_value.get.return_value = "abc"
    assert mock_backend_core.playlists.create("foobar") is None
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_delete_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlists.delete.return_value.get.side_effect = Exception
    assert not mock_backend_core.playlists.delete("dummy:/1")
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_lookup_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlists.lookup.return_value.get.side_effect = Exception
    assert mock_backend_core.playlists.lookup("dummy:/1") is None
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_lookup_bad_backends_backend_returns_none(mock_backend_core, playlists, logger):
    playlists.lookup.return_value.get.return_value = None
    assert mock_backend_core.playlists.lookup("dummy:/1") is None
    assert not logger.error.called


def test_lookup_bad_backends_backend_returns_wrong_type(
    mock_backend_core, playlists, logger
):
    playlists.lookup.return_value.get.return_value = "abc"
    assert mock_backend_core.playlists.lookup("dummy:/1") is None
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_refresh_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger, mocker
):
    send_mock = mocker.patch.object(CoreListener, "send")
    playlists.refresh.return_value.get.side_effect = Exception
    mock_backend_core.playlists.refresh()
    assert not send_mock.called
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_refresh_bad_backends_backend_raises_exception_called_with_uri(
    mock_backend_core, playlists, logger, mocker
):
    send_mock = mocker.patch.object(CoreListener, "send")
    playlists.refresh.return_value.get.side_effect = Exception
    mock_backend_core.playlists.refresh("dummy")
    assert not send_mock.called
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_save_bad_backends_backend_raises_exception(
    mock_backend_core, playlists, logger
):
    playlist = Playlist(uri="dummy:/1")
    playlists.save.return_value.get.side_effect = Exception
    assert mock_backend_core.playlists.save(playlist) is None
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_save_bad_backends_backend_returns_none(mock_backend_core, playlists, logger):
    playlist = Playlist(uri="dummy:/1")
    playlists.save.return_value.get.return_value = None
    assert mock_backend_core.playlists.save(playlist) is None
    assert not logger.error.called


def test_save_bad_backends_backend_returns_wrong_type(
    mock_backend_core, playlists, logger
):
    playlist = Playlist(uri="dummy:/1")
    playlists.save.return_value.get.return_value = "abc"
    assert mock_backend_core.playlists.save(playlist) is None
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)

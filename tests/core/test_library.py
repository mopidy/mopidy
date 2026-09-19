from unittest import mock

import pytest

from mopidy.backend import LibraryProvider
from mopidy.core import Core, _library
from mopidy.core import _validation as validation
from mopidy.models import Image, Ref, SearchResult, Track


@pytest.fixture
def library1():
    dummy1_root = Ref.directory(uri="dummy1:directory", name="dummy1")
    library1 = mock.Mock(spec=LibraryProvider)
    library1.get_images.return_value.get.return_value = {}
    library1.root_directory.get.return_value = dummy1_root
    return library1


@pytest.fixture
def backend1(library1):
    backend1 = mock.Mock()
    backend1.uri_schemes.get.return_value = ["dummy1"]
    backend1.actor_ref.actor_class.__name__ = "DummyBackend1"
    backend1.library = library1
    backend1.has_playlists.return_value.get.return_value = False
    return backend1


@pytest.fixture
def library2():
    dummy2_root = Ref.directory(uri="dummy2:directory", name="dummy2")
    library2 = mock.Mock(spec=LibraryProvider)
    library2.get_images.return_value.get.return_value = {}
    library2.root_directory.get.return_value = dummy2_root
    return library2


@pytest.fixture
def backend2(library2):
    backend2 = mock.Mock()
    backend2.uri_schemes.get.return_value = ["dummy2", "du2"]
    backend2.actor_ref.actor_class.__name__ = "DummyBackend2"
    backend2.library = library2
    backend2.has_playlists.return_value.get.return_value = False
    return backend2


@pytest.fixture
def backend3():
    # A backend without the optional library provider
    backend3 = mock.Mock()
    backend3.uri_schemes.get.return_value = ["dummy3"]
    backend3.actor_ref.actor_class.__name__ = "DummyBackend3"
    backend3.has_library.return_value.get.return_value = False
    backend3.has_library_browse.return_value.get.return_value = False
    return backend3


@pytest.fixture
def core(backend1, backend2, backend3):
    return Core(
        config={},
        mixer=None,
        backends=[backend1, backend2, backend3],
    )


# TODO: split by method
def test_get_images_returns_empty_dict_for_no_uris(core):
    assert core.library.get_images([]) == {}


def test_get_images_returns_empty_result_for_unknown_uri(core):
    result = core.library.get_images(["dummy4:track"])
    assert result == {"dummy4:track": ()}


def test_get_images_returns_empty_result_for_library_less_uri(core):
    result = core.library.get_images(["dummy3:track"])
    assert result == {"dummy3:track": ()}


def test_get_images_maps_uri_to_backend(core, library1, library2):
    core.library.get_images(["dummy1:track"])
    library1.get_images.assert_called_once_with(["dummy1:track"])
    library2.get_images.assert_not_called()


def test_get_images_maps_uri_to_backends(core, library1, library2):
    core.library.get_images(["dummy1:track", "dummy2:track"])
    library1.get_images.assert_called_once_with(["dummy1:track"])
    library2.get_images.assert_called_once_with(["dummy2:track"])


def test_get_images_returns_images(core, library1):
    library1.get_images.return_value.get.return_value = {
        "dummy1:track": [Image(uri="uri")],
    }

    result = core.library.get_images(["dummy1:track"])
    assert result == {"dummy1:track": (Image(uri="uri"),)}


def test_get_images_merges_results(core, library1, library2):
    library1.get_images.return_value.get.return_value = {
        "dummy1:track": [Image(uri="uri1")],
    }
    library2.get_images.return_value.get.return_value = {
        "dummy2:track": [Image(uri="uri2")],
    }

    result = core.library.get_images(
        ["dummy1:track", "dummy2:track", "dummy3:track", "dummy4:track"],
    )
    expected = {
        "dummy1:track": (Image(uri="uri1"),),
        "dummy2:track": (Image(uri="uri2"),),
        "dummy3:track": (),
        "dummy4:track": (),
    }
    assert expected == result


def test_browse_root_returns_dir_ref_for_each_lib_with_root_dir_name(
    core, library1, library2, backend3
):
    result = core.library.browse(None)

    assert result == [
        Ref.directory(uri="dummy1:directory", name="dummy1"),
        Ref.directory(uri="dummy2:directory", name="dummy2"),
    ]
    assert not library1.browse.called
    assert not library2.browse.called
    assert not backend3.library.browse.called


def test_browse_empty_string_returns_nothing(core, library1, library2):
    result = core.library.browse("")

    assert result == []
    assert not library1.browse.called
    assert not library2.browse.called


def test_browse_dummy1_selects_dummy1_backend(core, library1, library2):
    library1.browse.return_value.get.return_value = [
        Ref.directory(uri="dummy1:directory:/foo/bar", name="bar"),
        Ref.track(uri="dummy1:track:/foo/baz.mp3", name="Baz"),
    ]

    core.library.browse("dummy1:directory:/foo")

    assert library1.browse.call_count == 1
    assert library2.browse.call_count == 0
    library1.browse.assert_called_with("dummy1:directory:/foo")


def test_browse_dummy2_selects_dummy2_backend(core, library1, library2):
    library2.browse.return_value.get.return_value = [
        Ref.directory(uri="dummy2:directory:/bar/baz", name="quux"),
        Ref.track(uri="dummy2:track:/bar/foo.mp3", name="Baz"),
    ]

    core.library.browse("dummy2:directory:/bar")

    assert library1.browse.call_count == 0
    assert library2.browse.call_count == 1
    library2.browse.assert_called_with("dummy2:directory:/bar")


def test_browse_dummy3_returns_nothing(core, library1, library2):
    result = core.library.browse("dummy3:test")

    assert result == []
    assert library1.browse.call_count == 0
    assert library2.browse.call_count == 0


def test_browse_dir_returns_subdirs_and_tracks(core, library1):
    library1.browse.return_value.get.return_value = [
        Ref.directory(uri="dummy1:directory:/foo/bar", name="Bar"),
        Ref.track(uri="dummy1:track:/foo/baz.mp3", name="Baz"),
    ]

    result = core.library.browse("dummy1:directory:/foo")
    assert result == [
        Ref.directory(uri="dummy1:directory:/foo/bar", name="Bar"),
        Ref.track(uri="dummy1:track:/foo/baz.mp3", name="Baz"),
    ]


def test_lookup_returns_empty_dict_for_no_uris(core):
    assert core.library.lookup(uris=[]) == {}


def test_lookup_can_handle_uris(core, library1, library2):
    track1 = Track(uri="dummy1:a", name="abc")
    track2 = Track(uri="dummy2:a", name="def")

    library1.lookup_many().get.return_value = {"dummy1:a": [track1]}
    library2.lookup_many().get.return_value = {"dummy2:a": [track2]}

    result = core.library.lookup(uris=["dummy1:a", "dummy2:a"])
    assert result == {
        "dummy2:a": [track2],
        "dummy1:a": [track1],
    }


def test_lookup_uris_returns_empty_list_for_dummy3_track(core, library1, library2):
    result = core.library.lookup(uris=["dummy3:a"])

    assert result == {
        "dummy3:a": [],
    }
    assert not library1.lookup.called
    assert not library2.lookup.called


def test_lookup_batches_uris(core, library1, library2):
    track1 = Track(uri="dummy1:a", name="abc")
    track2 = Track(uri="dummy1:b", name="def")
    track3 = Track(uri="dummy2:a", name="ghi")
    track4 = Track(uri="dummy2:b", name="jkl")

    library1.lookup_many.return_value.get.return_value = {
        "dummy1:a": [track1],
        "dummy1:b": [track2],
    }
    library2.lookup_many.return_value.get.return_value = {
        "dummy2:a": [track3],
        "dummy2:b": [track4],
    }

    result = core.library.lookup(
        uris=[
            "dummy1:a",
            "dummy1:b",
            "dummy2:a",
            "dummy2:b",
        ],
    )

    library1.lookup_many.assert_called_once_with(["dummy1:a", "dummy1:b"])
    library2.lookup_many.assert_called_once_with(["dummy2:a", "dummy2:b"])

    assert result == {
        "dummy1:a": [track1],
        "dummy1:b": [track2],
        "dummy2:a": [track3],
        "dummy2:b": [track4],
    }


def test_refresh_with_uri_selects_dummy1_backend(core, library1, library2):
    core.library.refresh("dummy1:a")

    library1.refresh.assert_called_once_with("dummy1:a")
    assert not library2.refresh.called


def test_refresh_with_uri_selects_dummy2_backend(core, library1, library2):
    core.library.refresh("dummy2:a")

    assert not library1.refresh.called
    library2.refresh.assert_called_once_with("dummy2:a")


def test_refresh_with_uri_fails_silently_for_dummy3_uri(core, library1, library2):
    core.library.refresh("dummy3:a")

    assert not library1.refresh.called
    assert not library2.refresh.called


def test_refresh_without_uri_calls_all_backends(core, library1, library2):
    core.library.refresh()

    library1.refresh.return_value.get.assert_called_once_with()
    library2.refresh.return_value.get.assert_called_once_with()


def test_search_combines_results_from_all_backends(core, library1, library2):
    track1 = Track(uri="dummy1:a")
    track2 = Track(uri="dummy2:a")
    result1 = SearchResult(tracks=[track1])
    result2 = SearchResult(tracks=[track2])

    library1.search.return_value.get.return_value = result1
    library2.search.return_value.get.return_value = result2

    result = core.library.search({"any": ["a"]})

    assert result1 in result
    assert result2 in result
    library1.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )
    library2.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )


def test_search_with_uris_selects_dummy1_backend(core, library1, library2):
    core.library.search(
        query={"any": ["a"]},
        uris=["dummy1:", "dummy1:foo", "dummy3:"],
    )

    library1.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=["dummy1:", "dummy1:foo"],
        exact=False,
    )
    assert not library2.search.called


def test_search_with_uris_selects_both_backends(core, library1, library2):
    core.library.search(
        query={"any": ["a"]},
        uris=["dummy1:", "dummy1:foo", "dummy2:"],
    )

    library1.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=["dummy1:", "dummy1:foo"],
        exact=False,
    )
    library2.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=["dummy2:"],
        exact=False,
    )


def test_search_filters_out_none(core, library1, library2):
    track1 = Track(uri="dummy1:a")
    result1 = SearchResult(tracks=[track1])

    library1.search.return_value.get.return_value = result1
    library2.search.return_value.get.return_value = None

    result = core.library.search({"any": ["a"]})

    assert result1 in result
    assert None not in result
    library1.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )
    library2.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )


def test_search_accepts_query_dict_instead_of_kwargs(core, library1, library2):
    track1 = Track(uri="dummy1:a")
    track2 = Track(uri="dummy2:a")
    result1 = SearchResult(tracks=[track1])
    result2 = SearchResult(tracks=[track2])

    library1.search.return_value.get.return_value = result1
    library2.search.return_value.get.return_value = result2

    result = core.library.search({"any": ["a"]})

    assert result1 in result
    assert result2 in result
    library1.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )
    library2.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )


def test_search_normalises_bad_queries(core, library1):
    core.library.search({"any": "foobar"})
    library1.search.assert_called_once_with(
        query={"any": ["foobar"]},
        uris=None,
        exact=False,
    )


def test_get_distinct_with_query(core, library1, library2):
    library1.get_distinct.return_value.get.return_value = {}
    library2.get_distinct.return_value.get.return_value = {}

    result = core.library.get_distinct("album", {"any": ["a"]})

    library1.get_distinct.assert_called_with("album", {"any": ["a"]})
    library2.get_distinct.assert_called_with("album", {"any": ["a"]})
    assert result == set()


def test_get_distinct_combines_results_from_all_backends(core, library1, library2):
    result1 = "foo"
    result2 = "bar"
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {result2}

    result = core.library.get_distinct("artist")

    assert result1 in result
    assert result2 in result


def test_get_distinct_combined_results_are_unique(core, library1, library2):
    result1 = "foo"
    result2 = "foo"
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {result2}

    result = core.library.get_distinct("artist")

    assert result1 in result
    assert len(result) == 1


def test_get_distinct_checks_field_is_valid(core, mocker):
    check_choice_mock = mocker.patch.object(_library.validation, "check_choice")
    core.library.get_distinct("artist")
    check_choice_mock.assert_called_with(
        "artist",
        validation.DISTINCT_FIELDS.keys(),
    )


def test_get_distinct_any_field_raises_valueerror(core):
    with pytest.raises(ValueError):
        core.library.get_distinct("any")


def test_get_distinct_unknown_tag_in_query_raises_valueerror(core):
    with pytest.raises(ValueError):
        core.library.get_distinct("album", {"track": ["a"]})


def test_get_distinct_track_name_field_maps_to_track_for_backwards_compatibility(
    core, library1, library2
):
    result1 = "foo"
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {}

    result = core.library.get_distinct("track_name")

    library1.get_distinct.assert_called_with("track", None)
    library2.get_distinct.assert_called_with("track", None)
    assert result == {result1}


def test_get_distinct_track_field_is_deprecated(core, library1, library2):
    result1 = "bar"
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {}

    with pytest.deprecated_call():
        assert core.library.get_distinct("track") == {result1}


def test_get_distinct_validate_integer_results(core, library1, library2, mocker):
    logger_mock = mocker.patch.object(_library, "logger")
    result1 = 99
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {}

    assert core.library.get_distinct("track_no") == {result1}
    assert core.library.get_distinct("disc_no") == {result1}
    logger_mock.error.assert_not_called()

    assert core.library.get_distinct("uri") == set()
    logger_mock.error.assert_called_once()


def test_get_distinct_wrong_result_types_removed_and_logged(
    core, library1, library2, mocker
):
    logger_mock = mocker.patch.object(_library, "logger")
    result1 = 99
    library1.get_distinct.return_value.get.return_value = {result1}
    library2.get_distinct.return_value.get.return_value = {}

    assert core.library.get_distinct("track_no") == {result1}
    logger_mock.error.assert_not_called()

    result2 = "foo"
    library2.get_distinct.return_value.get.return_value = {result2}

    assert core.library.get_distinct("track_no") == {result1}
    logger_mock.error.assert_called_once()

    logger_mock.error.reset_mock()
    assert core.library.get_distinct("uri") == {result2}
    logger_mock.error.assert_called()


@pytest.fixture
def legacy_backend():
    legacy_backend = mock.Mock()
    legacy_backend.actor_ref.actor_class.__name__ = "DummyBackend"
    legacy_backend.uri_schemes.get.return_value = ["dummy"]
    legacy_backend.library = mock.Mock(spec=LibraryProvider)
    return legacy_backend


@pytest.fixture
def legacy_core(legacy_backend):
    return Core(config={}, mixer=None, backends=[legacy_backend])


def test_legacy_core_search_call_backend_search_with_exact(legacy_core, legacy_backend):
    legacy_core.library.search(query={"any": ["a"]})
    legacy_backend.library.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=False,
    )


def test_legacy_core_search_with_exact_call_backend_search_with_exact(
    legacy_core, legacy_backend
):
    legacy_core.library.search(query={"any": ["a"]}, exact=True)
    legacy_backend.library.search.assert_called_once_with(
        query={"any": ["a"]},
        uris=None,
        exact=True,
    )


def test_legacy_core_search_with_handles_legacy_backend(legacy_core, legacy_backend):
    legacy_backend.library.search.return_value.get.side_effect = TypeError
    legacy_core.library.search(query={"any": ["a"]}, exact=True)
    # We are just testing that this doesn't fail.


@pytest.fixture
def library():
    dummy_root = Ref.directory(uri="dummy:directory", name="dummy")
    library = mock.Mock(spec=LibraryProvider)
    library.root_directory.get.return_value = dummy_root
    return library


@pytest.fixture
def backend(library):
    backend = mock.Mock()
    backend.actor_ref.actor_class.__name__ = "DummyBackend"
    backend.uri_schemes.get.return_value = ["dummy"]
    backend.library = library
    return backend


@pytest.fixture
def mock_backend_core(backend):
    return Core(config={}, mixer=None, backends=[backend])


@pytest.fixture
def logger(mocker):
    return mocker.patch.object(_library, "logger")


def test_browse_bad_backend_backend_raises_exception_for_root(
    mock_backend_core, library, logger
):
    # Might happen if root_directory is a property for some weird reason.
    library.root_directory.get.side_effect = Exception
    assert mock_backend_core.library.browse(None) == []
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_browse_bad_backend_backend_returns_none_for_root(
    mock_backend_core, library, logger
):
    library.root_directory.get.return_value = None
    assert mock_backend_core.library.browse(None) == []
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_browse_bad_backend_backend_returns_wrong_type_for_root(
    mock_backend_core, library, logger
):
    library.root_directory.get.return_value = 123
    assert mock_backend_core.library.browse(None) == []
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_browse_bad_backend_backend_raises_exception_for_browse(
    mock_backend_core, library, logger
):
    library.browse.return_value.get.side_effect = Exception
    assert mock_backend_core.library.browse("dummy:directory") == []
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_browse_bad_backend_backend_returns_wrong_type_for_browse(
    mock_backend_core, library, logger
):
    library.browse.return_value.get.return_value = [123]
    assert mock_backend_core.library.browse("dummy:directory") == []
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_distinct_bad_backend_backend_raises_exception(
    mock_backend_core, library, logger
):
    library.get_distinct.return_value.get.side_effect = Exception
    assert set() == mock_backend_core.library.get_distinct("artist")
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_get_distinct_bad_backend_backend_returns_none(
    mock_backend_core, library, logger
):
    library.get_distinct.return_value.get.return_value = None
    assert set() == mock_backend_core.library.get_distinct("artist")
    assert not logger.error.called


def test_get_distinct_bad_backend_backend_returns_wrong_type(
    mock_backend_core, library, logger
):
    library.get_distinct.return_value.get.return_value = "abc"
    assert set() == mock_backend_core.library.get_distinct("artist")
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_distinct_bad_backend_backend_returns_iterable_containing_wrong_types(
    mock_backend_core, library, logger
):
    library.get_distinct.return_value.get.return_value = [1, 2, 3]
    assert set() == mock_backend_core.library.get_distinct("artist")
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_images_bad_backend_backend_raises_exception(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.side_effect = Exception
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_get_images_bad_backend_backend_returns_none(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.return_value = None
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    assert not logger.error.called


def test_get_images_bad_backend_backend_returns_wrong_type(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.return_value = "abc"
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_images_bad_backend_backend_returns_mapping_containing_wrong_types(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.return_value = {uri: "abc"}
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_images_bad_backend_backend_returns_mapping_containing_none(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.return_value = {uri: None}
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_get_images_bad_backend_backend_returns_unknown_uri(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.get_images.return_value.get.return_value = {"foo": []}
    assert mock_backend_core.library.get_images([uri]) == {uri: ()}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_lookup_by_uris_bad_backend_backend_raises_exception(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.lookup_many.return_value.get.side_effect = Exception
    assert mock_backend_core.library.lookup(uris=[uri]) == {uri: []}
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_lookup_by_uris_bad_backend_backend_returns_none(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.lookup_many.return_value.get.return_value = None
    assert mock_backend_core.library.lookup(uris=[uri]) == {uri: []}
    assert not logger.error.called


def test_lookup_by_uris_bad_backend_backend_returns_wrong_type(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.lookup_many.return_value.get.return_value = [
        Track(uri=uri, name="abc"),
    ]
    assert mock_backend_core.library.lookup(uris=[uri]) == {uri: []}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_lookup_by_uris_bad_backend_backend_returns_iterable_containing_wrong_types(
    mock_backend_core, library, logger
):
    uri = "dummy:/1"
    library.lookup_many.return_value.get.return_value = {uri: [123]}
    assert mock_backend_core.library.lookup(uris=[uri]) == {uri: []}
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)


def test_refresh_bad_backend_backend_raises_exception(
    mock_backend_core, library, logger
):
    library.refresh.return_value.get.side_effect = Exception
    mock_backend_core.library.refresh()
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_refresh_bad_backend_backend_raises_exception_with_uri(
    mock_backend_core, library, logger
):
    library.refresh.return_value.get.side_effect = Exception
    mock_backend_core.library.refresh("dummy:/1")
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_search_bad_backend_backend_raises_exception(
    mock_backend_core, library, logger
):
    library.search.return_value.get.side_effect = Exception
    assert mock_backend_core.library.search(query={"any": ["foo"]}) == []
    logger.exception.assert_called_with(mock.ANY, "DummyBackend")


def test_search_bad_backend_backend_raises_lookuperror(
    mock_backend_core, library, logger
):
    # TODO: is this behavior desired? Do we need to continue handling
    # LookupError case specially.
    library.search.return_value.get.side_effect = LookupError
    with pytest.raises(LookupError):
        mock_backend_core.library.search(query={"any": ["foo"]})


def test_search_bad_backend_backend_returns_none(mock_backend_core, library, logger):
    library.search.return_value.get.return_value = None
    assert mock_backend_core.library.search(query={"any": ["foo"]}) == []
    assert not logger.error.called


def test_search_bad_backend_backend_returns_wrong_type(
    mock_backend_core, library, logger
):
    library.search.return_value.get.return_value = "abc"
    assert mock_backend_core.library.search(query={"any": ["foo"]}) == []
    logger.error.assert_called_with(mock.ANY, "DummyBackend", mock.ANY)

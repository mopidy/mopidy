from importlib.metadata import version

import pytest

import mopidy


def test_version_attribute_is_deprecated():
    with pytest.deprecated_call():
        result = mopidy.__version__

    assert result == version("mopidy")


def test_unknown_attribute_raises_attribute_error():
    with pytest.raises(AttributeError, match="no attribute 'foo'"):
        _ = mopidy.foo  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[unresolved-attribute]

import pydantic
import pytest

from mopidy.types import Uri
from tests.factories import ImageFactory


def test_uri():
    uri = "an_uri"
    image = ImageFactory.build(uri=uri)
    assert image.uri == uri
    with pytest.raises(pydantic.ValidationError):
        image.uri = Uri("")


def test_width():
    image = ImageFactory.build(uri="uri", width=100)
    assert image.width == 100
    with pytest.raises(pydantic.ValidationError):
        image.width = None


def test_height():
    image = ImageFactory.build(uri="uri", height=100)
    assert image.height == 100
    with pytest.raises(pydantic.ValidationError):
        image.height = None

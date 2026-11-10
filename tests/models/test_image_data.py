import json

import pydantic
import pytest

from mopidy._exts.http import jsonrpc
from mopidy.models import ImageData

BINARY = bytes(range(256))


def test_data_and_mime_type():
    image_data = ImageData(data=BINARY, mime_type="image/png")

    assert image_data.data == BINARY
    assert image_data.mime_type == "image/png"


def test_mime_type_defaults_to_none():
    assert ImageData(data=b"x").mime_type is None


def test_is_immutable():
    image_data = ImageData(data=b"x")

    with pytest.raises(pydantic.ValidationError):
        image_data.data = b"y"


def test_repr_does_not_include_data():
    assert "data" not in repr(ImageData(data=BINARY, mime_type="image/png"))


def test_serialize_encodes_data_as_base64():
    image_data = ImageData(data=b"\xff\xd8\xff", mime_type="image/jpeg")

    assert image_data.serialize() == {
        "__model__": "ImageData",
        "data": "/9j/",
        "mime_type": "image/jpeg",
    }


def test_json_round_trip():
    image_data = ImageData(data=BINARY, mime_type="image/png")

    result = ImageData.model_validate_json(image_data.model_dump_json(by_alias=True))

    assert result == image_data


def test_replace_keeps_binary_data():
    image_data = ImageData(data=BINARY, mime_type="image/png")

    result = image_data.replace(mime_type="image/x-png")

    assert result.data == BINARY
    assert result.mime_type == "image/x-png"


def test_invalid_base64_is_rejected():
    with pytest.raises(pydantic.ValidationError):
        ImageData.model_validate_json('{"data": "not base64!"}')


def test_jsonrpc_response_encodes_data_as_base64():
    wrapper = jsonrpc.Wrapper(
        objects={"image": lambda: ImageData(data=BINARY, mime_type="image/png")},
    )

    response = wrapper.handle_json(b'{"jsonrpc": "2.0", "id": 1, "method": "image"}')

    assert response is not None
    result = json.loads(response)["result"]
    assert result["__model__"] == "ImageData"
    assert ImageData.model_validate(result).data == BINARY

from typing import Any, ClassVar, Self, TypeVar

import msgspec

T = TypeVar("T")


class ModelRegistry:
    _models: ClassVar[dict[str, type]] = {}

    @classmethod
    def add(cls, model: type[T]) -> type[T]:
        cls._models[model.__name__] = model
        return model

    @classmethod
    def get(cls, name: str) -> type:
        return cls._models[name]


class BaseModel(
    msgspec.Struct,
    frozen=True,
    omit_defaults=True,
    repr_omit_defaults=True,
    tag_field="__model__",
    tag=True,
):
    """Base class for all models."""

    def replace(self, **kwargs: Any) -> Self:
        """Return a new instance with updated fields."""
        current_fields = msgspec.structs.asdict(self)
        updated_fields = {**current_fields, **kwargs}
        return type(self)(**updated_fields)

    def serialize(self) -> dict[str, Any]:
        """Serialize the model to a dict."""
        return msgspec.to_builtins(self)

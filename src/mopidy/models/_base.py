from typing import Any, Self

import pydantic
from pydantic.config import ConfigDict


class BaseModel(pydantic.BaseModel):
    """Base class for all models."""

    model_config = ConfigDict(
        # Forbid extra fields in the model.
        extra="forbid",
        # Do not allow the model to be mutated after creation.
        frozen=True,
    )

    def replace(self, **updated_fields: Any) -> Self:
        """Return a new instance with updated fields."""
        fields = self.model_dump(mode="json", by_alias=False, exclude_unset=True)
        fields |= updated_fields
        return self.__class__(**fields)

    def serialize(self) -> dict[str, Any]:
        """Serialize the model to a dict."""
        return self.model_dump(mode="json", by_alias=True, exclude_none=True)

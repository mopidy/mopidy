from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Any


type RegistryEntry = type[Any] | dict[str, Any]


class Registry(Mapping):
    """Registry of components provided by Mopidy extensions.

    Passed to the :meth:`~Extension.setup` method of all extensions. The
    registry can be used like a dict of string keys and lists.

    Some keys have a special meaning, including, but not limited to:

    - ``backend`` is used for Mopidy backend classes.
    - ``frontend`` is used for Mopidy frontend classes.

    Extensions can use the registry for allow other to extend the extension
    itself. For example the ``Mopidy-Local`` historically used the
    ``local:library`` key to allow other extensions to register library
    providers for ``Mopidy-Local`` to use. Extensions should namespace
    custom keys with the extension's :attr:`~Extension.ext_name`,
    e.g. ``local:foo`` or ``http:bar``.
    """

    def __init__(self) -> None:
        self._registry: dict[str, list[RegistryEntry]] = {}

    def add(self, name: str, entry: RegistryEntry) -> None:
        """Add a component to the registry.

        Multiple classes can be registered to the same name.
        """
        self._registry.setdefault(name, []).append(entry)

    def __getitem__(self, name: str) -> list[RegistryEntry]:
        return self._registry.setdefault(name, [])

    def __iter__(self) -> Iterator[str]:
        return iter(self._registry)

    def __len__(self) -> int:
        return len(self._registry)

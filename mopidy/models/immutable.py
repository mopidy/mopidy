import copy
import itertools
import weakref

from mopidy.models.fields import Field

# Registered models for automatic deserialization
_models = {}


class ImmutableObject:
    """
    Superclass for immutable objects whose fields can only be modified via the
    constructor.

    This version of this class has been retained to avoid breaking any clients
    relying on it's behavior. Internally in Mopidy we now use
    :class:`ValidatedImmutableObject` for type safety and it's much smaller
    memory footprint.

    :param kwargs: kwargs to set as fields on the object
    :type kwargs: any
    """

    # Any sub-classes that don't set slots won't be effected by the base using
    # slots as they will still get an instance dict.
    __slots__ = ["__weakref__"]

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if not self._is_valid_field(key):
                raise TypeError(
                    f"__init__() got an unexpected keyword argument {key!r}"
                )
            self._set_field(key, value)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError("Object is immutable.")

    def __delattr__(self, name):
        if name.startswith("_"):
            object.__delattr__(self, name)
        else:
            raise AttributeError("Object is immutable.")

    def _is_valid_field(self, name):
        return hasattr(self, name) and not callable(getattr(self, name))

    def _set_field(self, name, value):
        if value == getattr(self.__class__, name):
            self.__dict__.pop(name, None)
        else:
            self.__dict__[name] = value

    def _items(self):
        return self.__dict__.items()

    def __repr__(self):
        kwarg_pairs = []
        for key, value in sorted(self._items()):
            if isinstance(value, (frozenset, tuple)):
                if not value:
                    continue
                value = list(value)
            kwarg_pairs.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(kwarg_pairs)})"

    def __hash__(self):
        hash_sum = 0
        for key, value in self._items():
            hash_sum += hash(key) + hash(value)
        return hash_sum

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return all(
            a == b
            for a, b in itertools.zip_longest(
                self._items(), other._items(), fillvalue=object()
            )
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def replace(self, **kwargs):
        """
        Replace the fields in the model and return a new instance

        Examples::

            # Returns a track with a new name
            Track(name='foo').replace(name='bar')
            # Return an album with a new number of tracks
            Album(num_tracks=2).replace(num_tracks=5)

        :param kwargs: kwargs to set as fields on the object
        :type kwargs: any
        :rtype: instance of the model with replaced fields
        """
        other = copy.copy(self)
        for key, value in kwargs.items():
            if not self._is_valid_field(key):
                raise TypeError(
                    f"replace() got an unexpected keyword argument {key!r}"
                )
            other._set_field(key, value)
        return other

    def serialize(self):
        data = {}
        data["__model__"] = self.__class__.__name__
        for key, value in self._items():
            if isinstance(value, (set, frozenset, list, tuple)):
                value = [
                    v.serialize() if isinstance(v, ImmutableObject) else v
                    for v in value
                ]
            elif isinstance(value, ImmutableObject):
                value = value.serialize()
            if not (isinstance(value, list) and len(value) == 0):
                data[key] = value
        return data


class _ValidatedImmutableObjectMeta(type):

    """Helper that initializes fields, slots and memoizes instance creation."""

    def __new__(cls, name, bases, attrs):
        fields = {}

        for base in bases:  # Copy parent fields over to our state
            fields.update(getattr(base, "_fields", {}))

        for key, value in attrs.items():  # Add our own fields
            if isinstance(value, Field):
                fields[key] = "_" + key
                value._name = key

        attrs["_fields"] = fields
        attrs["_instances"] = weakref.WeakValueDictionary()
        attrs["__slots__"] = list(attrs.get("__slots__", [])) + list(
            fields.values()
        )

        clsc = super().__new__(cls, name, bases, attrs)

        if clsc.__name__ != "ValidatedImmutableObject":
            _models[clsc.__name__] = clsc

        return clsc

    def __call__(cls, *args, **kwargs):  # noqa: N805
        instance = super().__call__(*args, **kwargs)
        return cls._instances.setdefault(weakref.ref(instance), instance)


class ValidatedImmutableObject(
    ImmutableObject, metaclass=_ValidatedImmutableObjectMeta
):
    """
    Superclass for immutable objects whose fields can only be modified via the
    constructor. Fields should be :class:`Field` instances to ensure type
    safety in our models.

    Note that since these models can not be changed, we heavily memoize them
    to save memory. So constructing a class with the same arguments twice will
    give you the same instance twice.
    """

    __slots__ = ["_hash"]

    def __hash__(self):
        if not hasattr(self, "_hash"):
            hash_sum = super().__hash__()
            object.__setattr__(self, "_hash", hash_sum)
        return self._hash

    def _is_valid_field(self, name):
        return name in self._fields

    def _set_field(self, name, value):
        object.__setattr__(self, name, value)

    def _items(self):
        for field, key in self._fields.items():
            if hasattr(self, key):
                yield field, getattr(self, key)

    def replace(self, **kwargs):
        """
        Replace the fields in the model and return a new instance

        Examples::

            # Returns a track with a new name
            Track(name='foo').replace(name='bar')
            # Return an album with a new number of tracks
            Album(num_tracks=2).replace(num_tracks=5)

        Note that internally we memoize heavily to keep memory usage down given
        our overly repetitive data structures. So you might get an existing
        instance if it contains the same values.

        :param kwargs: kwargs to set as fields on the object
        :type kwargs: any
        :rtype: instance of the model with replaced fields
        """
        if not kwargs:
            return self
        other = super().replace(**kwargs)
        if hasattr(self, "_hash"):
            object.__delattr__(other, "_hash")
        return self._instances.setdefault(weakref.ref(other), other)

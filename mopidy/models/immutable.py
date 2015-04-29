from __future__ import absolute_import, unicode_literals

import copy
import inspect
import itertools
import weakref

from mopidy.models.fields import Field
from mopidy.utils import deprecation


class ImmutableObjectMeta(type):

    """Helper to automatically assign field names to descriptors."""

    def __new__(cls, name, bases, attrs):
        fields = {}
        for key, value in attrs.items():
            if isinstance(value, Field):
                fields[key] = '_' + key
                value._name = key

        attrs['_fields'] = fields
        attrs['_instances'] = weakref.WeakValueDictionary()
        attrs['__slots__'] = list(attrs.get('__slots__', []))
        attrs['__slots__'].extend(['_hash'] + fields.values())

        for ancestor in [b for base in bases for b in inspect.getmro(base)]:
            if '__weakref__' in getattr(ancestor, '__slots__', []):
                break
        else:
            attrs['__slots__'].append('__weakref__')

        return super(ImmutableObjectMeta, cls).__new__(cls, name, bases, attrs)

    def __call__(cls, *args, **kwargs):  # noqa: N805
        instance = super(ImmutableObjectMeta, cls).__call__(*args, **kwargs)
        return cls._instances.setdefault(weakref.ref(instance), instance)


class ImmutableObject(object):

    """
    Superclass for immutable objects whose fields can only be modified via the
    constructor. Fields should be :class:`Field` instances to ensure type
    safety in our models.

    Note that since these models can not be changed, we heavily memoize them
    to save memory. So constructing a class with the same arguments twice will
    give you the same instance twice.

    :param kwargs: kwargs to set as fields on the object
    :type kwargs: any
    """

    __metaclass__ = ImmutableObjectMeta

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if key not in self._fields:
                raise TypeError(
                    '__init__() got an unexpected keyword argument "%s"' %
                    key)
            super(ImmutableObject, self).__setattr__(key, value)

    def __setattr__(self, name, value):
        if name in self.__slots__:
            return super(ImmutableObject, self).__setattr__(name, value)
        raise AttributeError('Object is immutable.')

    def __delattr__(self, name):
        if name in self.__slots__:
            return super(ImmutableObject, self).__delattr__(name)
        raise AttributeError('Object is immutable.')

    def _items(self):
        for field, key in self._fields.items():
            if hasattr(self, key):
                yield field, getattr(self, key)

    def __repr__(self):
        kwarg_pairs = []
        for key, value in sorted(self._items()):
            if isinstance(value, (frozenset, tuple)):
                if not value:
                    continue
                value = list(value)
            kwarg_pairs.append('%s=%s' % (key, repr(value)))
        return '%(classname)s(%(kwargs)s)' % {
            'classname': self.__class__.__name__,
            'kwargs': ', '.join(kwarg_pairs),
        }

    def __hash__(self):
        if not hasattr(self, '_hash'):
            hash_sum = 0
            for key, value in self._items():
                hash_sum += hash(key) + hash(value)
            super(ImmutableObject, self).__setattr__('_hash', hash_sum)
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return all(a == b for a, b in itertools.izip_longest(
            self._items(), other._items(), fillvalue=object()))

    def __ne__(self, other):
        return not self.__eq__(other)

    def copy(self, **values):
        """
        .. deprecated:: 1.1
            Use :meth:`replace` instead. Note that we no longer return copies.
        """
        deprecation.warn('model.immutable.copy')
        return self.replace(**values)

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
        other = copy.copy(self)
        for key, value in kwargs.items():
            if key not in self._fields:
                raise TypeError(
                    'copy() got an unexpected keyword argument "%s"' % key)
            super(ImmutableObject, other).__setattr__(key, value)
        super(ImmutableObject, other).__delattr__('_hash')
        return self._instances.setdefault(weakref.ref(other), other)

    def serialize(self):
        data = {}
        data['__model__'] = self.__class__.__name__
        for key, value in self._items():
            if isinstance(value, (set, frozenset, list, tuple)):
                value = [
                    v.serialize() if isinstance(v, ImmutableObject) else v
                    for v in value]
            elif isinstance(value, ImmutableObject):
                value = value.serialize()
            if not (isinstance(value, list) and len(value) == 0):
                data[key] = value
        return data

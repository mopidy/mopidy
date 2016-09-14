from __future__ import absolute_import, unicode_literals

from mopidy import compat


class Field(object):

    """
    Base field for use in
    :class:`~mopidy.models.immutable.ValidatedImmutableObject`. These fields
    are responsible for type checking and other data sanitation in our models.

    For simplicity fields use the Python descriptor protocol to store the
    values in the instance dictionary. Also note that fields are mutable if
    the object they are attached to allow it.

    Default values will be validated with the exception of :class:`None`.

    :param default: default value for field
    :param type: if set the field value must be of this type
    :param choices: if set the field value must be one of these
    """

    def __init__(self, default=None, type=None, choices=None):
        self._name = None  # Set by ValidatedImmutableObjectMeta
        self._choices = choices
        self._default = default
        self._type = type

        if self._default is not None:
            self.validate(self._default)

    def validate(self, value):
        """Validate and possibly modify the field value before assignment"""
        if self._type and not isinstance(value, self._type):
            raise TypeError('Expected %s to be a %s, not %r' %
                            (self._name, self._type, value))
        if self._choices and value not in self._choices:
            raise TypeError('Expected %s to be a one of %s, not %r' %
                            (self._name, self._choices, value))
        return value

    def __get__(self, instance, owner):
        if not instance:
            return self
        return getattr(instance, '_' + self._name, self._default)

    def __set__(self, instance, value):
        if value is not None:
            value = self.validate(value)

        if value is None or value == self._default:
            self.__delete__(instance)
        else:
            setattr(instance, '_' + self._name, value)

    def __delete__(self, instance):
        if hasattr(instance, '_' + self._name):
            delattr(instance, '_' + self._name)


class String(Field):

    """
    Specialized :class:`Field` which is wired up for bytes and unicode.

    :param default: default value for field
    """

    def __init__(self, default=None):
        # TODO: normalize to unicode?
        # TODO: only allow unicode?
        # TODO: disallow empty strings?
        super(String, self).__init__(type=compat.string_types, default=default)


class Date(String):
    """
    :class:`Field` for storing ISO 8601 dates as a string.

    Supported formats are ``YYYY-MM-DD``, ``YYYY-MM`` and ``YYYY``, currently
    not validated.

    :param default: default value for field
    """
    pass  # TODO: make this check for YYYY-MM-DD, YYYY-MM, YYYY using strptime.


class Identifier(String):
    """
    :class:`Field` for storing values such as GUIDs or other identifiers.

    Values will be interned.

    :param default: default value for field
    """
    def validate(self, value):
        value = super(Identifier, self).validate(value)
        if isinstance(value, compat.text_type):
            value = value.encode('utf-8')
        return compat.intern(value)


class URI(Identifier):
    """
    :class:`Field` for storing URIs

    Values will be interned, currently not validated.

    :param default: default value for field
    """
    pass  # TODO: validate URIs?


class Integer(Field):
    """
    :class:`Field` for storing integer numbers.

    :param default: default value for field
    :param min: field value must be larger or equal to this value when set
    :param max: field value must be smaller or equal to this value when set
    """

    def __init__(self, default=None, min=None, max=None):
        self._min = min
        self._max = max
        super(Integer, self).__init__(
            type=compat.integer_types, default=default)

    def validate(self, value):
        value = super(Integer, self).validate(value)
        if self._min is not None and value < self._min:
            raise ValueError('Expected %s to be at least %d, not %d' %
                             (self._name, self._min, value))
        if self._max is not None and value > self._max:
            raise ValueError('Expected %s to be at most %d, not %d' %
                             (self._name, self._max, value))
        return value


class Boolean(Field):
    """
    :class:`Field` for storing boolean values

    :param default: default value for field
    """

    def __init__(self, default=None):
        super(Boolean, self).__init__(type=bool, default=default)


class Collection(Field):
    """
    :class:`Field` for storing collections of a given type.

    :param type: all items stored in the collection must be of this type
    :param container: the type to store the items in
    """

    def __init__(self, type, container=tuple):
        super(Collection, self).__init__(type=type, default=container())

    def validate(self, value):
        if isinstance(value, compat.string_types):
            raise TypeError('Expected %s to be a collection of %s, not %r'
                            % (self._name, self._type.__name__, value))
        for v in value:
            if not isinstance(v, self._type):
                raise TypeError('Expected %s to be a collection of %s, not %r'
                                % (self._name, self._type.__name__, value))
        return self._default.__class__(value) or None

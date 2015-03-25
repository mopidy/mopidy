from __future__ import absolute_import, unicode_literals

import logging

logger = logging.getLogger(__name__)

try:
    import dbus
except ImportError:
    dbus = None

from mopidy import compat


# XXX: Hack to workaround introspection bug caused by gnome-keyring, should be
# fixed by version 3.5 per:
# https://git.gnome.org/browse/gnome-keyring/commit/?id=5dccbe88eb94eea9934e2b7
if dbus:
    EMPTY_STRING = dbus.String('', variant_level=1)
else:
    EMPTY_STRING = ''


FETCH_ERROR = (
    'Fetching passwords from your keyring failed. Any passwords '
    'stored in the keyring will not be available.')


def fetch():
    if not dbus:
        logger.debug('%s (dbus not installed)', FETCH_ERROR)
        return []

    try:
        bus = dbus.SessionBus()
    except dbus.exceptions.DBusException as e:
        logger.debug('%s (%s)', FETCH_ERROR, e)
        return []

    if not bus.name_has_owner('org.freedesktop.secrets'):
        logger.debug(
            '%s (org.freedesktop.secrets service not running)', FETCH_ERROR)
        return []

    service = _service(bus)
    session = service.OpenSession('plain', EMPTY_STRING)[1]
    items, locked = service.SearchItems({'service': 'mopidy'})

    if not locked and not items:
        return []

    if locked:
        # There is a chance we can unlock without prompting the users...
        items, prompt = service.Unlock(locked)
        if prompt != '/':
            _prompt(bus, prompt).Dismiss()
            logger.debug('%s (Keyring is locked)', FETCH_ERROR)
            return []

    result = []
    secrets = service.GetSecrets(items, session, byte_arrays=True)
    for item_path, values in secrets.items():
        session_path, parameters, value, content_type = values
        attrs = _item_attributes(bus, item_path)
        result.append((attrs['section'], attrs['key'], bytes(value)))
    return result


def set(section, key, value):
    """Store a secret config value for a given section/key.

    Indicates if storage failed or succeeded.
    """
    if not dbus:
        logger.debug('Saving %s/%s to keyring failed. (dbus not installed)',
                     section, key)
        return False

    try:
        bus = dbus.SessionBus()
    except dbus.exceptions.DBusException as e:
        logger.debug('Saving %s/%s to keyring failed. (%s)', section, key, e)
        return False

    if not bus.name_has_owner('org.freedesktop.secrets'):
        logger.debug(
            'Saving %s/%s to keyring failed. '
            '(org.freedesktop.secrets service not running)',
            section, key)
        return False

    service = _service(bus)
    collection = _collection(bus)
    if not collection:
        return False

    if isinstance(value, compat.text_type):
        value = value.encode('utf-8')

    session = service.OpenSession('plain', EMPTY_STRING)[1]
    secret = dbus.Struct((session, '', dbus.ByteArray(value),
                          'plain/text; charset=utf8'))
    label = 'mopidy: %s/%s' % (section, key)
    attributes = {'service': 'mopidy', 'section': section, 'key': key}
    properties = {'org.freedesktop.Secret.Item.Label': label,
                  'org.freedesktop.Secret.Item.Attributes': attributes}

    try:
        item, prompt = collection.CreateItem(properties, secret, True)
    except dbus.exceptions.DBusException as e:
        # TODO: catch IsLocked errors etc.
        logger.debug('Saving %s/%s to keyring failed. (%s)', section, key, e)
        return False

    if prompt == '/':
        return True

    _prompt(bus, prompt).Dismiss()
    logger.debug('Saving secret %s/%s failed. (Keyring is locked)',
                 section, key)
    return False


def _service(bus):
    return _interface(bus, '/org/freedesktop/secrets',
                      'org.freedesktop.Secret.Service')


# NOTE: depending on versions and setup 'default' might not exists, so try and
# use it but fall back to the 'login' collection, and finally the 'session' one
# if all else fails. We should probably create a keyring/collection setting
# that allows users to set this so they have control over where their secrets
# get stored.
def _collection(bus):
    for name in 'aliases/default', 'collection/login', 'collection/session':
        path = '/org/freedesktop/secrets/' + name
        if _collection_exists(bus, path):
            break
    else:
        return None
    return _interface(bus, path, 'org.freedesktop.Secret.Collection')


# NOTE: Hack to probe if a given collection actually exists. Needed to work
# around an introspection bug in setting passwords for non-existant aliases.
def _collection_exists(bus, path):
    try:
        item = _interface(bus, path, 'org.freedesktop.DBus.Properties')
        item.Get('org.freedesktop.Secret.Collection', 'Label')
        return True
    except dbus.exceptions.DBusException:
        return False


# NOTE: We could call prompt.Prompt('') to unlock the keyring when it is not
# '/', but we would then also have to arrange to setup signals to wait until
# this has been completed. So for now we just dismiss the prompt and expect
# keyrings to be unlocked.
def _prompt(bus, path):
    return _interface(bus, path, 'Prompt')


def _item_attributes(bus, path):
    item = _interface(bus, path, 'org.freedesktop.DBus.Properties')
    result = item.Get('org.freedesktop.Secret.Item', 'Attributes')
    return dict((bytes(k), bytes(v)) for k, v in result.items())


def _interface(bus, path, interface):
    obj = bus.get_object('org.freedesktop.secrets', path)
    return dbus.Interface(obj, interface)

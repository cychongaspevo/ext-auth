from __future__ import unicode_literals
import importlib
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

USER_SETTINGS = getattr(settings, 'EXT_AUTH_SETTINGS', None)

DEFAULTS = {
    'FIREBASE_ADMIN_CERT': ''
}

MANDATORY = (
    'FIREBASE_ADMIN_CERT',
)

def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    elif "." in val:
        return import_from_string(val, setting_name)
    else:
        raise ImproperlyConfigured("Bad value for %r: %r" % (setting_name, val))


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = val.split(".")
        module_path, class_name = ".".join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = "Could not import %r for setting %r. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)

class ExtAuthSettings(object):
    
    def __init__(self, user_settings=None, defaults=None, mandatory=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.mandatory = mandatory or ()

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError("Invalid ExtAuth setting: %r" % (attr))

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        self.validate_setting(attr, val)

        # Cache the result
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError("ExtAuth setting: %r is mandatory" % (attr))

ext_auth_settings = ExtAuthSettings(USER_SETTINGS, DEFAULTS, MANDATORY)

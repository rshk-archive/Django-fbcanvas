"""Settings for Django-fbcanvas.

The purpose of this module is to provide default values and validation
to standard settings, along with some documentation on the settings themselves.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

## Load settings ---------------------------------------------------------------

## App ID and App Secret, from the Facebook App settings
FACEBOOK_APP_ID = getattr(settings, 'FACEBOOK_APP_ID', None)
FACEBOOK_APP_SECRET = getattr(settings, 'FACEBOOK_APP_SECRET', None)

## Default permissions that will be asked when the user first
## authorizes the application
FACEBOOK_DEFAULT_SCOPE = getattr(settings, 'FACEBOOK_DEFAULT_SCOPE', ['email', 'user_about_me', 'user_birthday'])

## URL to the Canvas Page for this app. Used for redirects
FACEBOOK_CANVAS_PAGE = getattr(settings, 'FACEBOOK_CANVAS_PAGE', None)

## Whether to force execution of the application inside canvas.
## This is accomplished by redirecting the user to the canvas page,
## either if the request is not signed or via JavaScript if we are not
## running inside a frame
FACEBOOK_FORCE_CANVAS = getattr(settings, 'FACEBOOK_FORCE_CANVAS', True)
FACEBOOK_FORCE_CANVAS_SIGNED = getattr(settings, 'FACEBOOK_FORCE_CANVAS_SIGNED', False)
FACEBOOK_FORCE_CANVAS_JSFRAME = getattr(settings, 'FACEBOOK_FORCE_CANVAS_JSFRAME', True)


## Validate settings -----------------------------------------------------------

required_settings = ['FACEBOOK_APP_ID', 'FACEBOOK_APP_SECRET']
for setting_name in required_settings:
    if not locals().get(setting_name):
        raise ImproperlyConfigured("%s must be defined in the settings while using django_fbcanvas." % setting_name)

"""django_fbcanvas - signals"""

from django.dispatch import Signal

## Sent after first registration of an user via Facebook
facebook_user_registered = Signal(providing_args=['user', 'facebook_data'])

## Sent by FacebookRequestMiddleware if request_ids are received.
## Allows attaching of hooks to handle requests (usually this will
## end up in a redirect to some request handling page)
facebook_app_request_received = Signal(providing_args=['request_ids'])

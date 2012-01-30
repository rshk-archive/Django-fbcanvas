"""URLs for Django-fbcanvas.

Be sure to ``include()`` these URLs somewhere, e.g. under ``facebook/``.
"""

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('django_facebook.views',
    url(r'^oauth/$', 'fb_oauth', name='facebook_oauth'),
    url(r'^deauthorize/$', 'fb_deauthorize', name='facebook_deauthorize'),
)

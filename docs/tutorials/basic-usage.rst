################################################################################
Basic usage of django_fbcanvas
################################################################################

This is a quick tutorial about using Django-fbcanvas in your application.


Changes to ``settings.py``
==========================

Add ``django_fbattle`` to your installed applications::

    INSTALLED_APPS = (
        ...
        'django_fbcanvas',
    )

Add ``django_fbcanvas.middleware.FacebookRequestMiddleware`` middleware.

.. NOTE::
    You should place this **before** ``CsrfViewMiddleware``
    in order to skip CSRF in case a valid signed request was received.

::

    MIDDLEWARE_CLASSES = (
        ...
        'django_fbcanvas.middleware.FacebookRequestMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        ...
    )
    

Add authentication backend::

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'django_fbcanvas.auth_backends.FacebookBackend',
    )


Django-fbcanvas specific settings::

    FACEBOOK_APP_ID = ""
    FACEBOOK_APP_SECRET = ""
    FACEBOOK_CANVAS_URL = ""


Decorators
==========

The only decorator supported at the moment is ``@facebook_required``,
from ``django_fbcanvas.decorators``.

Applied to a view, will require OAuth in case the user is either
non-authenticated or not associated to a Facebook user.

It will also catch authentication-related exceptions (such as the
ones for access_token expired and missing permissions) and redirect
to the OAuth page, if that's the case.

.. autofunction:: django_fbcanvas.decorators.facebook_required
    :noindex:



Using the API
=============

TODO: Write this


Handling application requests
=============================

TODO: Write this


Using signed requests
=====================

TODO: Write this


Tokens for ``offline_access``
=============================

Using this kind of tokens simplifies things a lot, but users may not
all agree to grant us unlimited access to their accounts..

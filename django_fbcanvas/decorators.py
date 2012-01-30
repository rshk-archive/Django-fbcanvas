"""django_fbcanvas - decorators"""

import logging

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs
from django.utils.functional import wraps

from django_fbcanvas import settings as fb_settings
from django_fbcanvas.utils import str_to_list
from django_fbcanvas.exceptions import OpenFacebookException
from django_fbcanvas.fb_api import oauth_start

logger = logging.getLogger(__name__)


def facebook_required(view_func=None, scope=fb_settings.FACEBOOK_DEFAULT_SCOPE,
                      redirect_field_name=REDIRECT_FIELD_NAME, login_url=None,
                      extra_params=None):
    """Decorator which makes the view require the given Facebook
    permissions, redirecting to the authorization page if necessary.

    .. NOTE::
       This implementation sends a request to check that the user
       has the required permissions before executing the view.
       
       This should be able to prevent most failures, but it will slow
       down things as an additional HTTP request will be performed
       on each request..

    :param view_func: The view function that will be decorated
    :param scope: List of names of permissions that will be required
    :param redirect_field_name:
    :param login_url: URL of the login page, in case permissions
        checking fails.
    :param extra_params: Extra paramters to be added to redirect_uri
    """
    #from django_facebook.utils import test_permissions
    if scope:
        scope_list = str_to_list(scope, separator=",")
    else:
        scope_list = fb_settings.FACEBOOK_DEFAULT_SCOPE
    
    def actual_decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            
            ## If the user is not logged in -> go to oauth
            ## If the logged-in user is not connected with facebook -> go to oauth
            
            if not request.user.is_authenticated() \
                or not request.user.facebookuser.access_token:
                return oauth_start(request, scope=scope_list)
            
            
            return view_func(request, *args, **kwargs)
            
            try:
                return view_func(request, *args, **kwargs)
            except OpenFacebookException, e:
                ## Check whether the user has required permissions
                ## if so, re-raise exception.
                ## Else, redirect to oauth url
                
                return oauth_start(request, scope=scope_list)
            
#            oauth_url, redirect_uri = get_oauth_url(request, scope_list)
#            if test_permissions(request, scope_list, redirect_uri):
#                return view_func(request, *args, **kwargs)
#            else:
#                logger.info('requesting access with redirect uri: %s', redirect_uri)
#                _canvas = canvas # Bring into local scope
#                if _canvas is None:
#                    _canvas = getattr(request, 'fb_info', {}).get('is_canvas', False)
#                response = response_redirect(oauth_url, canvas=_canvas)
#                return response
        return _wrapped_view

    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


#def facebook_required_lazy(view_func=None,
#                           scope=fb_settings.FACEBOOK_DEFAULT_SCOPE,
#                           redirect_field_name=REDIRECT_FIELD_NAME,
#                           login_url=None, extra_params=None, canvas=None):
#    """Decorator which makes the view require the given Facebook
#    permissions, redirecting to the authorization page if necessary.
#    
#    This implementation performs redirect upon caught exception,
#    instead of checking before acting; faster, but more prone to bugs.
#    
#    :param view_func: The view function that will be decorated
#    :param scope: List of names of permissions that will be required
#    :param redirect_field_name:
#    :param login_url: URL of the login page, in case permissions
#        checking fails.
#    :param extra_params: Extra paramters to be added to redirect_uri
#    :param canvas: Whether we are running inside canvas or not.
#        If not specified, its value will be determined at runtime
#        from ``request.fb_info['is_canvas']``.
#    """
#    from django_facebook.utils import test_permissions
#    from open_facebook import exceptions as open_facebook_exceptions
#    scope_list = parse_scope(scope)
#
#    def actual_decorator(view_func):
#        @wraps(view_func, assigned=available_attrs(view_func))
#        def _wrapped_view(request, *args, **kwargs):
#            oauth_url, redirect_uri = get_oauth_url(request, scope_list, extra_params=extra_params)
#            try:
#                ## Call get_persistent_graph() and convert the
#                ## token with correct redirect URI
#                get_persistent_graph(request, redirect_uri=redirect_uri)
#                return view_func(request, *args, **kwargs)
#            except open_facebook_exceptions.OpenFacebookException, e:
#                if test_permissions(request, scope_list, redirect_uri):
#                    ## An error if we already have permissions
#                    ## shouldn't have been caught
#                    ## raise to prevent bugs with error mapping to cause issues
#                    raise
#                else:
#                    logger.info(u'Requesting access with redirect_uri: %s, error was %s', redirect_uri, e)
#                    _canvas = canvas # Bring into local scope
#                    if _canvas is None:
#                        _canvas = getattr(request, 'fb_info', {}).get('is_canvas', False)
#                    response = response_redirect(oauth_url, canvas=_canvas)
#                    return response
#        return _wrapped_view
#
#    if view_func:
#        return actual_decorator(view_func)
#    return actual_decorator
#
#
#def facebook_connect_required():
#    """Decorator which makes the view require that the user
#    is registered within your application using Facebook.
#    
#    .. WARNING:: This decorator has not been implemented yet!
#    """
#    ## TODO: Write this :)
#    pass

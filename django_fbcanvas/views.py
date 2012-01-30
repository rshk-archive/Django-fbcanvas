"""Django-fbcanvas - Standard Views"""

import logging
logger = logging.getLogger(__name__)

from django.contrib import messages
from django.http import HttpResponseNotAllowed, HttpResponseRedirect,\
    HttpResponse

from django_fbcanvas.fb_api import oauth_start, oauth_at_from_code


def fb_oauth(request):
    """View to process the OAuth login via Facebook.
    
    This view accepts a GET argument "next" to specify the page where
    to go upon successful OAuth authentication.
    This defaults to '/' in order to prevent infinite redirects.
    """

    ## Check for error responses
    error_info = {
        'error': request.GET.get('error') or None,
        'error_reason': request.GET.get('error_reason') or None,
        'error_description': request.GET.get('error_description') or None,
    }
    
    if error_info['error']:
        if error_info['error_reason'] == 'user_denied':
            messages.warning(request, "You must click on the 'Authorize' button in order to log in with Facebook!")
        else:
            messages.error(request,
                           "An error occurred while trying to authenticate on Facebook: %s (%s)" \
                           % (error_info['error_reason'], error_info['error_description']))
        return HttpResponseRedirect("/")
    
    
    ## Check for OAuth "code" (after redirect from dialog)
    oauth_code = request.GET.get('code') or None
    if not oauth_code:
        return oauth_start(request, redirect_to="/")
    else:
        if request.REQUEST.get('state') == request.session['facebook_oauth_state']:
            result = oauth_at_from_code(code=oauth_code, redirect_uri="/")
            access_token = result['access_token']
            request.session['facebook_access_token'] = access_token
            request.fb_info['access_token'] = access_token
            
            ## TODO: Trigger a signal here
            
            _next = request.REQUEST.get('next') or '/'
            return HttpResponseRedirect(_next)
        else:
            ## This is a serious thing - do not ignore (but maybe just
            ## send a message to the user, instead of a scary white page?)
            raise HttpResponseNotAllowed("State doesn't match - you might be victim of CSRF")


def fb_deauthorize(request):
    """Deauthorize callback, pinged when an user deauthorizes this app."""
    
    ## TODO: Verify the signed request
    ## TODO: Trigger a signal
    
    ## Send a "thank you" message. We are polite even with robots. :)
    return HttpResponse("Thank you!")

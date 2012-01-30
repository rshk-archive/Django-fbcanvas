"""django_fbcanvas - middleware"""

import logging
from django_fbcanvas.user_mgmt import connect_user
logger = logging.getLogger(__name__)

import django_fbcanvas.settings as facebook_settings
from django_fbcanvas.utils import parse_signed_data
 

class FacebookRequestMiddleware:
    def process_request(self, request):
        """Process requests for Facebook apps. This is expecially
        useful for canvas apps, since it handles signed_request logins,
        application requests, etc.
        
        Information about the current interaction status with Facebook
        is stored into ``request.fb_info`` as a dict with following
        keys:
        
        - ``is_canvas`` - Whether we are running inside canvas or not.
          This is determined by the presence of a signed request
          via POST.
        - ``is_signed_request`` - Whether we received a signed request,
          either via POST parameter (canvas) or cookie (js sdk method).
        - ``signed_request_type`` - ``"post"`` or ``"cookie"``
        - ``app_request_ids`` - If a ``request_ids`` GET was passed,
          the IDs of requests to be processed.
        - ``is_authenticated`` - Whether we have a valid access_token
          for this user, or not.
        
        - Validate signed requests from Facebook
          - Login when running in canvas
          - For the deauthorize_callback ping
        - Process the requests execution when a request_ids parameter
          is passed -> redirect to somewhere
        - We should also prevent CSRF code to be checked if the request
          is using ``signed_request``.
        
        .. NOTE::
            This middleware should go before CsrfMiddleware in order
            to skip CSRF validation for POSTs inside canvas apps,
            in case a valid signed_request was received.
        """
        
        logger.debug("Running FacebookRequest Middleware")
        
        ## Add some facebook-related information to request
        request.fb_info = {
            "is_canvas": False,
            "is_signed_request": None,
            "signed_request_type": None,
            "app_request_ids": None,
            "is_authenticated": None,
            "access_token": None,
        }
        
        ## Check signed request ------------------------------------------------
        _sr_from = None
        _sr_data = None
        
        if request.POST.has_key('signed_request'):
            logger.debug("Got a signed_request via POST")
            _sr_from = 'post'
            _sr_data = request.POST['signed_request']
        elif request.GET.has_key('signed_request'):
            logger.debug("Got a signed_request via GET -- strange, but valid..")
            _sr_from = 'get'
            _sr_data = request.GET['signed_request']
        else:
            cookie_name = 'fbsr_%s' % facebook_settings.FACEBOOK_APP_ID
            cookie_data = request.COOKIES.get(cookie_name)
            if cookie_data:
                logger.debug("Got a signed_request via cookie")
                _sr_from = 'cookie'
                _sr_data = cookie_data
        
        if _sr_data:
            logger.debug("Parsing signed request: %r" % _sr_data)
            parsed_data = parse_signed_data(_sr_data)
            if parsed_data:
                
                ##--------------------------------------------------------------
                ## TODO: To avoid parsing the whole stuff each time
                ##       we should just check the ``user_id`` in the
                ##       received data. If the user is already logged in,
                ##       and the Facebook ID matches, just skip all the
                ##       verification stuff, unless specifically needed..
                ##-------------------------------------------------------------- 
                
                logger.debug("Valid signed data: %r" % parsed_data)
                if _sr_from in ('post', 'get'):
                    request.fb_info['is_canvas'] = True
                request.fb_info['is_signed_request'] = True
                request.fb_info['signed_request_type'] = _sr_from
                request.fb_info['access_token'] = parsed_data['oauth_token']
                request.fb_info['user_id'] = parsed_data['user_id']
                
                ## Parsed data usually looks like this:
                ## WARNING! We need some permissions to get email|a_t|etc..!!
                ##{'user_id': '1136957613',
                ##  'algorithm': 'HMAC-SHA256',
                ##  'expires': 1327874400,
                ##  'oauth_token': '--- the goddamn token here ---',
                ##  'user': {'locale': 'en_US', 'country': 'it', 'age': {'min': 21}},
                ##  'issued_at': 1327868027
                ##  }
                
                ## Skip CSRF validation in case of valid signed request
                request.csrf_processing_done = True
                
                ## TODO: Log in the user
                connect_user(request, facebook_id=parsed_data['user_id'])
        
        ## --- Application requests --------------------------------------------
        if request.REQUEST.has_key('request_ids'):
            request.fb_info['app_request_ids'] = request.REQUEST['request_ids'].split(',')
            ##TODO: Emit the facebook_app_request_received signal here


        return###===================================== STOP HERE ===============
        

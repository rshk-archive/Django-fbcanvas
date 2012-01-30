"""django_fbcanvas - fb_api

Utilities to connect to Facebook API"""

import logging
import urllib, urllib2

from django.http import QueryDict, HttpResponseRedirect

import django_fbcanvas.exceptions as facebook_exceptions
from django_fbcanvas.utils import encode_params, to_int, json, str_to_list
from django.core.urlresolvers import reverse
import django_fbcanvas.settings as fb_settings
import uuid
import hashlib
import re

logger = logging.getLogger(__name__)

def get_facebook(request, access_token=None):
    """Returns an instantiated OpenFacebook, taking access token
    from ``request.fb_info``.
    """
    
    if not access_token:
        try:
            ## Get fresh access token from signed request
            access_token = request.fb_info['access_token']
        except:
            pass
    
    if not access_token:
        try:
            ## Get (stale?) access token from database
            access_token = request.user.facebookuser.access_token
        except:
            pass
    
    logger.debug("Returning an OpenFacebook with access_token: %s" % access_token)
    
    ## TODO: If the access_token is expired, raise an exception an redirect to OAuth
            
    return OpenFacebook(access_token=access_token)
    

def oauth_start(request, scope=None, redirect_to=None):
    """Redirect to appropriate OAuth view in order to start
    OAuth login procedure / permission asking.
    
    :param scope: List of permissions to require
    :param redirect_to: Page where to redirect after OAuth.
        Defaults to current page.
    """
    
    ## Redirect URL, where to go after click in dialog
    ## This is our fb_oauth view
    redirect_to = request.build_absolute_uri(next)
    _oauth_page = reverse('django_fbcanvas.views.fb_oauth')
    _args = QueryDict("", True)
    _args['next'] = redirect_to
    _oauth_page += "?%s" % _args.urlencode()
    
    ## Permissions to be asked (aka SCOPE)
    if scope is None:
        scope = fb_settings.FACEBOOK_DEFAULT_SCOPE
    else:
        scope = str_to_list(scope)
    
    ## State, for CSRF prevention
    _state = str(hashlib.md5(uuid.uuid1()).hexdigest())
    request.session['facebook_oauth_state'] = _state
    
    ## Build OAuth dialog URL
    qd = QueryDict('', True)
    qd['client_id'] = fb_settings.FACEBOOK_APP_ID
    qd['redirect_uri'] = _oauth_page
    qd['state'] = _state
    qd['scope'] = scope
    
    dialog_url = "https://www.facebook.com/dialog/oauth?%s" % qd.urlencode()
    
    return HttpResponseRedirect(dialog_url)
    
def oauth_at_from_code(code, redirect_uri):
    """Converts an intermediate OAuth code into access_token"""
    return FacebookConnection.request(
        'oauth/access_token',
        client_id=fb_settings.FACEBOOK_APP_ID,
        client_secret=fb_settings.FACEBOOK_APP_SECRET,
        code=code,
        redirect_uri=redirect_uri)

def get_app_access_token():
    """
    Get the access_token for the app that can be used for
    insights and creating test users
    application_id = retrieved from the developer page
    application_secret = retrieved from the developer page
    returns the application access_token
    """
    kwargs = {
        'grant_type': 'client_credentials',
        'client_id': fb_settings.FACEBOOK_APP_ID,
        'client_secret': fb_settings.FACEBOOK_APP_SECRET,
    }
    response = FacebookConnection.request('oauth/access_token', **kwargs)
    return response['access_token']

def get_api_error_class(api_response):
    """Try to determine which error occurred exactly when dealing
    with Facebook APIs, and try to return an appropriate exception.
    
    See also: http://fbdevwiki.com/wiki/Error_codes
    """
    
    ## Token expired
    ##{u'error': {u'message': u'Error validating access token: Session has expired at unix time 1327874400. The current unix time is 1327889919.', u'type': u'OAuthException'}}
    
    if api_response.has_key('error'):
        error = api_response['error']
        if api_response.has_key('type') and api_response.has_key('message'):
            type, message = api_response['type'], api_response['message']
            if type == 'OAuthException':
                if re.match(r"^Error validating access token: Session has expired.*", message, re.IGNORECASE):
                    return facebook_exceptions.OAuthSessionExpired
                    pass
            pass
    
    pass

REQUEST_TIMEOUT = 8
REQUEST_ATTEMPTS = 2

class FacebookConnection(object):
    """Class for sending requests to Facebook and parsing
    the API response.
    """
    
    ## New API URL used for Graph API requests
    api_url = 'https://graph.facebook.com/'
    
    ## This older URL is still used for FQL requests
    old_api_url = 'https://api.facebook.com/method/'

    @classmethod
    def request(cls, path='', post_data=None, use_old_api_url=False, **params):
        """Main method used to send requests directly.
        
        :param path: The path for which to perform the request
        :param post_data: Data to be sent via POST
        :param use_old_api_url: Whether to use the old API url or the new one.
            Defaults to ``False`` (meaning use the new one).
        :param timeout: Timeout for the ``urllib2`` request
        :param attempts: Maximum number of attempts
        """
        
        api_base_url = cls.old_api_url if use_old_api_url else cls.api_url
        if getattr(cls, 'access_token', None):
            params['access_token'] = cls.access_token
        url = '%s%s?%s' % (api_base_url, path, urllib.urlencode(params))
        response = cls._request(url, post_data)
        return response

    @classmethod
    def _request(cls, url, post_data=None, timeout=REQUEST_TIMEOUT, attempts=REQUEST_ATTEMPTS):
        """Perform a HTTP request to the given URL and parse it as JSON.
        
        ``urllib2`` raises errors on different status codes so we
        use a ``try .. except`` clause here.
        """
        logger.info('requesting url %s with post data %s', url, post_data)
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Open Facebook Python')]
        # give it a few shots, connection is buggy at times

        encoded_params = encode_params(post_data) if post_data else None
        post_string = (urllib.urlencode(encoded_params) if post_data else None)
        
        response = None

        while attempts:
            response_file = None
            try:
                try:
                    ## For older Python versions you could leave out
                    ## the timeout
                    #response_file = opener.open(url, post_string)
                    response_file = opener.open(url, post_string, timeout=timeout)
                except (urllib2.HTTPError,), e:
                    ## Catch the silly status code errors
                    if 'http error' in str(e).lower():
                        response_file = e
                    else:
                        raise
                response = response_file.read().decode('utf8')
                break
            except (urllib2.HTTPError, urllib2.URLError), e:
                logger.warn('Facebook Graph API request: error or timeout: %s', unicode(e))
                attempts -= 1
                if attempts <= 0:
                    ## Maximum number of attempts reached, stop retrying 
                    raise
            finally:
                if response_file:
                    response_file.close()

        try:
            parsed_response = json.loads(response)
            logger.info('Facebook Graph API response: %s' % parsed_response)
        except Exception, e:
            ## Using generic Exception because we need to support
            ## multiple JSON libraries :S
            parsed_response = QueryDict(response, True)
            logger.info('Facebook Graph API response: %s' % parsed_response)

        if parsed_response and isinstance(parsed_response, dict):
            ## of course we have two different syntaxes
            if parsed_response.get('error'):
                cls.raise_error(parsed_response['error']['type'], parsed_response['error']['message'])
            elif parsed_response.get('error_code'):
                cls.raise_error(parsed_response['error_code'], parsed_response['error_msg'])

        return parsed_response

    @classmethod
    def raise_error(cls, error_type, message):
        """Search for a corresponding error class or fall back to
        generic :py:class:`django_fbcanvas.exceptions.OpenFacebookException`
        """
        import re
        error_class = None
        if not isinstance(error_type, int):
            error_class = getattr(facebook_exceptions, error_type, None)
        if error_class and not issubclass(error_class,
                                          facebook_exceptions.OpenFacebookException):
            error_class = None
        
        ## map error classes to facebook error IDs
        ## define a string to match a single error,
        ## use ranges for more complex cases
        ## also see http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
        
        ##----------------------------------------------------------------------
        ## Get all the exception classes from django_fbcanvas.exceptions
        ## that are subclass of OpenFacebookException and define a `codes`
        ## attribute (will contain error codes).
        ##----------------------------------------------------------------------
        exception_classes = sorted([
            e for e in [getattr(facebook_exceptions, e, None) for e in dir(facebook_exceptions)]
            if (getattr(e, 'codes', None) and issubclass(e, facebook_exceptions.OpenFacebookException))
        ], key=lambda e: e.range())

        ## Find the error code inside the message..
        ## TODO: Isn't there a better way to do this??
        error_code = None
        error_code_re = re.compile('\(#(\d+)\)')
        matches = error_code_re.match(message)
        matching_groups = matches.groups() if matches else None
        if matching_groups:
            error_code = to_int(matching_groups[0]) or None

        for class_ in exception_classes:
            codes_list = class_.codes_list()
            # match the error class
            matching_error_class = None
            for code in codes_list:
                if isinstance(code, basestring):
                    # match on string
                    key = code
                    if key in message:
                        matching_error_class = class_
                        break
                elif isinstance(code, tuple):
                    start, stop = code
                    if error_code and start <= error_code <= stop:
                        matching_error_class = class_
                        break
                elif isinstance(code, (int, long)):
                    if int(code) == error_code:
                        matching_error_class = class_
                        break
                else:
                    raise(
                        ValueError, 'Dont know how to handle %s of ' \
                        'type %s' % (code, type(code)))
            #tell about the happy news if we found something
            if matching_error_class:
                error_class = matching_error_class
                break

        if 'Missing' in message and 'parameter' in message:
            error_class = facebook_exceptions.MissingParameter

        if not error_class:
            error_class = facebook_exceptions.OpenFacebookException

        raise error_class(message)

class OpenFacebook(FacebookConnection):
    """Main object used to handle Facebook API requests.
    
    
    **Getting your authentication started**

    OpenFacebook gives you access to the facebook api.
    For most user related actions you need an access_token.
    There are 3 ways of getting a facebook access_token
    
    1. code is passed as request parameter and traded for an
       ``access_token`` using the api
    2. code is passed through a signed cookie and traded for an access_token
    3. access_token is passed directly (retrieved through javascript, which
       would be bad security, or through one of the mobile flows.)

    Requesting a code for flow 1 and 2 is quite easy. Facebook docs are here:
    http://developers.facebook.com/docs/authentication/

    **Client side code request**
    
    For the client side flow simply use the FB.login functionality
    and on the landing page call::
    
        facebook = get_facebook_graph(request)
        print facebook.me()

    **Server side code request**
    
    ::

        facebook = get_facebook_graph(request)
        print facebook.me()


    **Actually using the facebook API**

    After retrieving an access token API calls are relatively straigh forward

    Getting info about me::
    
        facebook.get('me')

    Learning some more about fashiolista::
    
        facebook.get('fashiolista')

    Writing your first comment::
    
        facebook.set('fashiolista/comments', message='I love Fashiolista!')

    Posting to a users wall::
    
        facebook.set('me/feed', message='check out fashiolista',
                 url='http://www.fashiolista.com')

    Liking a page::
    
        facebook.set('fashiolista/likes')

    Executing some FQL::
    
        facebook.fql('SELECT name FROM user WHERE uid = me()')

    Uploading pictures::
    
        photo_urls = [
            'http://e.fashiocdn.com/images/entities/0/7/B/I/9/0.365x365.jpg',
            'http://e.fashiocdn.com/images/entities/0/5/e/e/r/0.365x365.jpg',
        ]
        for photo in photo_urls:
            print facebook.set('me/feed', message='Check out Fashiolista',
                               picture=photo, url='http://www.fashiolista.com')
    """
    def __init__(self, access_token=None, prefetched_data=None,
                 expires=None, current_user_id=None):
        self.access_token = access_token
        
        ## extra data coming from signed cookies
        self.prefetched_data = prefetched_data

        ## store to enable detection for offline usage
        self.expires = expires

        ## Hook to store the current user id if representing the
        ## Facebook connection to a logged in user :)
        self.current_user_id = current_user_id

    def is_authenticated(self):
        """Check whether the current user is authenticated against Facebook"""
        try:
            me = self.me()
        except facebook_exceptions.OpenFacebookException:
            me = None
        authenticated = bool(me)
        return authenticated

    def get(self, path, **kwargs):
        """Performs a GET request on the Graph API"""
        response = self.request(path, **kwargs)
        return response
    
    def get_many(self, *ids, **kwargs):
        """Performs a "multiple" GET request on the Graph API"""
        kwargs['ids'] = ','.join(ids)
        return self.request(**kwargs)

    def post(self, path, params=None, **post_data):
        """Performs a POST request on the Graph API"""
        assert self.access_token, 'Write operations require an access token'
        if not params:
            params = {}
        params['method'] = 'post'

        response = self.request(path, post_data=post_data, **params)
        return response
    
    set = post ## Allow get/set usage
    update = post ## CRUD method name is UPDATE

    def delete(self, *args, **kwargs):
        """Performs a DELETE request on the Graph API"""
        kwargs['method'] = 'delete'
        self.request(*args, **kwargs)

    def fql(self, query, **kwargs):
        """Executes a FQL query using the Facebook FQL API"""
        kwargs['format'] = 'JSON'
        kwargs['query'] = query
        path = 'fql.query'
        response = self.request(path, use_old_api_url=True, **kwargs)
        return response

    def me(self):
        """Cached method of requesting information about me"""
        me = getattr(self, '_me', None)
        if me is None:
            self._me = me = self.get('me')
        return me

    def my_image_url(self, size=None):
        """
        Returns the image url from your profile
        """
        query_dict = QueryDict('', True)
        if size:
            query_dict['type'] = size
        query_dict['access_token'] = self.access_token

        url = '%sme/picture?%s' % (self.api_url, query_dict.urlencode())
        return url
    
    def get_permissions(self):
        """Get a list of permissions the user granted us"""
        perms = self.get('me/permissions')['data'][0]
        return sorted([p[0] for p in perms if p[1] == '1'])

    def request(self, path='', post_data=None, get_data=None, use_old_api_url=False, **params):
        """Main function for sending requests to Facebook APIs
        
        :param path: Either the object path for REST Graph API, or
            `fql.query` for FQL queries.
        :param post_data:
            Data to be sent via POST
        :param get_data:
            Data that will be used to build the GET query.
        :param use_old_api_url: If set to ``True``, uses the old API URL
            (still valid for FQL requests).
        
        Extra kwargs will be used to build the GET query.
        
        """
        api_base_url = self.api_url
        if use_old_api_url:
            api_base_url = self.old_api_url
        
        if not get_data:
            get_data = {}
        
        if getattr(self, 'access_token', None):
            params['access_token'] = self.access_token
        
        get_data.update(params)
        
        url = '%s%s%s' % (api_base_url, path, ("?%s" % urllib.urlencode(get_data)) if get_data else "")
        logger.debug('Requesting URL: %s', url)
        response = self._request(url, post_data)
        return response


class FacebookAuthorization(FacebookConnection):
    """Authorization stuff"""
    
    @classmethod
    def get_app_access_token(cls):
        """
        Get the access_token for the app that can be used for
        insights and creating test users
        application_id = retrieved from the developer page
        application_secret = retrieved from the developer page
        returns the application access_token
        """
        kwargs = {
            'grant_type': 'client_credentials',
            'client_id': fb_settings.FACEBOOK_APP_ID,
            'client_secret': fb_settings.FACEBOOK_APP_SECRET,
        }
        response = cls.request('oauth/access_token', **kwargs)
        return response['access_token']

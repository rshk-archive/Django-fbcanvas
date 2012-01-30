"""Django-fbcanvas - User management functions"""

import re
import logging
logger = logging.getLogger(__name__)

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify

from django_fbcanvas.fb_api import OpenFacebook
from django_fbcanvas.models import FacebookUser
from django_fbcanvas.utils import json


def _create_unique_username(base_username):
    """Create an unique username, by adding numbers at the end in
    order to ensure its uniqueness all over our db.
    """
    usernames = list(User.objects.filter(username__istartswith=base_username).values_list('username', flat=True))
    usernames_lower = [str(u).lower() for u in usernames]
    username = str(base_username)
    i = 1
    while base_username.lower() in usernames_lower:
        base_username = username + str(i)
        i += 1
    return base_username

def _create_username(value):
    """Create username from a name"""
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return (re.sub('[-\s]+', '-', value))

def _generate_password(size=20):
    """Generate a random password of given size"""
    import string
    from random import choice
    _ch_pool = string.letters + string.digits
    return ''.join([choice(_ch_pool) for i in range(size)])

def connect_user(request, facebook_id):
    """Connects an user logged-in via Facebook or, if no user
    was found, preoceed to register a new one.
    """
    
    logger.debug("Connecting user with facebook_id '%s'" % facebook_id)
    
    ## Try to retrieve user by Facebook id
    user = authenticate(facebook_id=int(facebook_id))
    
    if user:
        ## The user already exists -- just log in
        login(request, user)
        return user
    
    ## Register a new user
    try:
        access_token = request.fb_info['access_token']
    except:
        ## Was unable to retrieve access_token.
        ## Redirect to OAuth endpoint page.
        pass
    
    fbapi = OpenFacebook(access_token)
    fb_user = fbapi.get('me')
    
    ##--------------------------------------------------------------------------
    ## NOTE: Hereby we require the user to grant us ``email`` permission,
    ##       in order to access its email address. In case we want to
    ##       remove that requirement, we should allow registration of users
    ##       with dummy email address..
    ##--------------------------------------------------------------------------
    
    new_user_name = _create_unique_username(fb_user.get('username') or _create_username(fb_user['name']))
    new_user_email = fb_user['email']
    new_user_password = _generate_password(15) 
    
    new_user = User.objects.create_user(new_user_name, new_user_email, new_user_password)
    new_user.backend = 'django_facebook.auth_backends.FacebookBackend'
    
    new_fb_user = FacebookUser()
    new_fb_user.user = new_user
    new_fb_user.facebook_id = fb_user['id']
    new_fb_user.facebook_name = fb_user['name']
    new_fb_user.facebook_profile_data = json.dumps(fb_user)
    new_fb_user.access_token = access_token
    new_fb_user.facebook_profile_url = fb_user['link']
    new_fb_user.granted_permissions = ",".join(fbapi.get_permissions())
    new_fb_user.save()
    
    login(request, new_user)
    
    return new_user
    
    #new_user.backend = 'django_facebook.auth_backends.FacebookBackend'
    #auth.login(request, new_user)    
    
    
#    
#    
#    
#    
#    
#    
#    user = None
#    graph = facebook_graph or get_facebook_graph(request, access_token)
#    facebook = FacebookUserConverter(graph)
#
#    assert facebook.is_authenticated()
#    facebook_data = facebook.facebook_profile_data()
#    force_registration = request.REQUEST.get('force_registration') or\
#        request.REQUEST.get('force_registration_hard')
#
#    logger.debug('force registration is set to %s', force_registration)
#    if request.user.is_authenticated() and not force_registration:
#        action = CONNECT_ACTIONS.CONNECT
#        user = _connect_user(request, facebook)
#    else:
#        email = facebook_data.get('email', False)
#        email_verified = facebook_data.get('verified', False)
#        kwargs = {}
#        if email and email_verified:
#            kwargs = {'facebook_email': email}
#        auth_user = authenticate(facebook_id=facebook_data['id'], **kwargs)
#        if auth_user and not force_registration:
#            action = CONNECT_ACTIONS.LOGIN
#
#            # Has the user registered without Facebook, using the verified FB
#            # email address?
#            # It is after all quite common to use email addresses for usernames
#            if not auth_user.get_profile().facebook_id:
#                update = True
#            else:
#                update = getattr(auth_user, 'fb_update_required', False)
#            user = _login_user(request, facebook, auth_user, update=update)
#        else:
#            action = CONNECT_ACTIONS.REGISTER
#            # when force registration is active we should clearout
#            # the old profile
#            user = _register_user(request, facebook,
#                                  remove_old_connections=force_registration)
#
#    #store likes and friends if configured
#    sid = transaction.savepoint()
#    try:
#        if facebook_settings.FACEBOOK_STORE_LIKES:
#            facebook.get_and_store_likes(user)
#        if facebook_settings.FACEBOOK_STORE_FRIENDS:
#            facebook.get_and_store_friends(user)
#        transaction.savepoint_commit(sid)
#    except IntegrityError, e:
#        logger.warn(u'Integrity error encountered during registration, '
#                'probably a double submission %s' % e,
#            exc_info=sys.exc_info(), extra={
#            'request': request,
#            'data': {
#                 'body': unicode(e),
#             }
#        })
#        transaction.savepoint_rollback(sid)
#
#    profile = user.get_profile()
#    #store the access token for later usage if the profile model supports it
#    if hasattr(profile, 'access_token'):
#        # only update the access token if it is long lived and
#        # not equal to the current token
#        if not graph.expires and graph.access_token != profile.access_token:
#            # TODO, maybe we should just always do this.
#            profile.access_token = graph.access_token
#            profile.save()
#
#    return action, user

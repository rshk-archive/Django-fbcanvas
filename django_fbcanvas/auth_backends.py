"""django_fbcanvas - auth_backends"""

from django.contrib.auth import backends
from django_fbcanvas.models import FacebookUser

class FacebookBackend(backends.ModelBackend):
    """Authentication backend for use with Facebook users"""
    
    def authenticate(self, facebook_id=None):
        """Authenticate a Facebook user by facebook_id.
        
        This will look for the ``facebook_id`` inside ``FacebooUser``
        objects, and return the associated ``User``, if one was found.
        
        :param facebook_id: ID of the Facebook user.
        :returns: a ``django.contrib.auth.models.User`` or ``None``
        """
        
        if not facebook_id:
            return None
        
        _fbu_query = FacebookUser.objects.all().order_by('user').select_related('user')
        try:
            profile = _fbu_query.get(facebook_id=facebook_id)
        except FacebookUser.DoesNotExist:
            return None
        else:
            return profile.user
        
        #profiles = _fbu_query.filter(facebook_id=facebook_id)[:1]
        #profile = profiles[0] if profiles else None
        
        
        
        
#        if facebook_id:
#            profile_class = get_profile_class()
#            profile_query = profile_class.objects.all().order_by('user').select_related('user')
#            profile = None
#
#            ## Filter on email or ``facebook_id``, two queries for better
#            ## queryplan with large data sets
#            
#            if facebook_id:
#                profiles = profile_query.filter(facebook_id=facebook_id)[:1]
#                profile = profiles[0] if profiles else None
#            
#            if profile is None and facebook_email:
#                try:
#                    ## WARNING! We assume that all the user emails are verified
#                    profiles = profile_query.filter(user__email__iexact=facebook_email)[:1]
#                    profile = profiles[0] if profiles else None
#                except DatabaseError:
#                    try:
#                        user = models.User.objects.get(email=facebook_email)
#                    except models.User.DoesNotExist:
#                        user = None
#                    profile = user.get_profile() if user else None
#
#            if profile:
#                ## Populate the profile cache while we're getting it anyway
#                user = profile.user
#                user._profile = profile
#                return user

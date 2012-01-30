"""django_fbcanvas - models"""

from django.db import models
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User


class FacebookUser(models.Model):
    """Model used to store information about Facebook users and their
    relationship with ``django.auth`` users.
    
    We don't want to rely on the standard profile system for users, since
    that will require more code in the final application, and is more
    prone to errors.
    
    Instead, we store here all the information about the facebook/user
    relationship, etc.
    """
    
    ## The django auth User
    user = models.OneToOneField(User)
    
    ## Facebook ID of this user
    facebook_id = models.BigIntegerField(unique=True)
    
    ## Access token for the offline access. This is set only if
    ## the user granted us the offline_access permission.
    access_token = models.TextField(blank=True, help_text='Facebook token for offline access')
    
    ## Long name of the user, as seen on Facebook
    facebook_name = models.CharField(max_length=255, blank=True)
    
    ## URL to the user profile on Facebook
    facebook_profile_url = models.TextField(blank=True)
    
    ## Permissions the user granted us, as a comma-separated list
    granted_permissions = models.TextField(blank=True)
    
    ## JSON-encoded object containing information about the Facebook User.
    ## This is the as-is result from the Graph API request for the user.
    facebook_profile_data = models.TextField(blank=True)

    def __unicode__(self):
        return "[User: %s - FBUser: %s]" % (self.user.username, self.facebook_id)

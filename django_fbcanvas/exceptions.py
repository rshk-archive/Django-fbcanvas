"""django_fbcanvas - exceptions

See also: http://fbdevwiki.com/wiki/Error_codes#User_Permission_Errors
"""

import logging
logger = logging.getLogger(__name__)

class OpenFacebookException(Exception):
    """Base class for all the OpenFacebook exceptions"""

    @classmethod
    def codes_list(cls):
        """Returns the codes as a list of instructions"""
        if hasattr(cls, 'codes'):
            if isinstance(cls.codes, list):
                codes_list = cls.codes
            else:
                codes_list = [cls.codes]
            return codes_list

    @classmethod
    def range(cls):
        logger.warn("DEPRECATED METHOD OpenFacebookException.range() was called!! -- use 'errorcode_range()' instead!")
        return cls.errorcode_range()
    
    @classmethod
    def errorcode_range(cls):
        """Returns for how many codes this Exception, matches with
        the eventual goal of matching an error to the most specific
        error class.
        """
        ##TODO: Rename this something different from "range"!!!
        ec_range = 0
        codes_list = cls.codes_list()
        for c in codes_list:
            if isinstance(c, tuple):
                start, stop = c
                ec_range += stop - start + 1
            else:
                ec_range += 1

        #make sure none specific exceptions are last in the order
        if not ec_range:
            ec_range = 1000

        return ec_range


class ParameterException(OpenFacebookException):
    """Codes: 100-199"""
    codes = (100, 199)


class UnknownException(OpenFacebookException):
    """Raised when facebook itself don't know what went wrong"""
    codes = 1


class OAuthException(OpenFacebookException):
    """Base exception for OAuth errors"""
    pass

class OAuthSessionTimedOut(OAuthException):
    error_code = 450
    error_id = "API_EC_SESSION_TIMED_OUT"
    error_description = "Session key specified has passed its expiration time"
    
#450     API_EC_SESSION_TIMED_OUT     Session key specified has passed its expiration time
#451     API_EC_SESSION_METHOD     Session key specified cannot be used to call this method
#452     API_EC_SESSION_INVALID     Session key invalid. This could be because the session key has an incorrect format, or because the user has revoked this session
#453     API_EC_SESSION_REQUIRED     A session key is required for calling this method
#454     API_EC_SESSION_REQUIRED_FOR_SECRET     A session key must be specified when request is signed with a session secret
#455     API_EC_SESSION_CANNOT_USE_SESSION_SECRET     A session secret is not permitted to be used with this type of session key 

class PermissionException(OAuthException):
    """Codes: ``3,200-299``"""
    codes = [3, (200, 299)]

class UserPermissionException(PermissionException):
    """Codes: ``300-399``"""
    codes = (300, 399)


class FeedActionLimit(UserPermissionException):
    """When you posted too many times from one user account.
    
    Codes: ``341``
    """
    codes = 341


class DuplicateStatusMessage(OpenFacebookException):
    """Codes: ``506``"""
    codes = 506


class MissingParameter(OpenFacebookException):
    """Missing parameter"""
    pass


class AliasException(OpenFacebookException):
    """When you send a request to a non-existent URL, Facebook
    returns error code ``803``, instead of an HTTP ``404``..
    
    Codes: ``803``
    """
    codes = 803

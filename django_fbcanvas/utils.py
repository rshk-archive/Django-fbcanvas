"""django_fbcanvas - utils

Miscellaneous utility functions for django_fbcanvas
"""

import re
import logging
logger = logging.getLogger(__name__)

from django.conf import settings
from django.db import models

from django_fbcanvas import settings as fb_settings

## Look for and import an usable JSON library
try:
    from django.utils import simplejson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json


#def urlsafer_b64decode(s):
#    """URL-Safe Base64 decoding with auto-padding, since PHP doesn't
#    apply padding to encoded strings while Python module requires it.
#    """
#    import base64
#    s=s.strip()
#    print "urlsafer_b64decode: orig=",repr(s)
#    padding_factor = (4 - (len(s) % 4)) % 4
#    s += "=" * (padding_factor + 1) ## WTF ???
#    print "urlsafer_b64decode: padded=",repr(s)
#    #return base64.urlsafe_b64decode(unicode(s))
#    #return unicode(base64.b64decode(s)).translate({'+': u'-', '/': u'_'})
#    return base64.b64decode(s).translate({'+': u'-', '/': u'_'})

#def base64_url_decode_php_style(inp):
def urlsafer_b64decode(s):
    """Damn crap!
    
    
    PHP follows a slightly different protocol for base64 URL encoding,
    using ``-`` instead of ``+`` and ``_`` instead of ``/``.
    Also, it doesn't use ``=`` for padding.
    
    For a full explanation see:
    http://stackoverflow.com/questions/3302946/how-to-base64-url-decode-in-python
    and http://sunilarora.org/parsing-signedrequest-parameter-in-python-bas
    
    :param inp: The base64-encoded string to be decoded
    """
    import base64
    padding_factor = (4 - len(s) % 4) % 4
    s += "=" * padding_factor
    return base64.b64decode(unicode(s).translate(dict(zip(map(ord, u'-_'), u'+/'))))


def str_to_list(s, separator=","):
    """Convert a separated string to a list.
    
    If ``s`` is a basestring, returns it splitted using ``separator``.
    Else, just passes it to the ``list()`` constructor.
    """
    if isinstance(s, basestring):
        return s.split(separator)
    else:
        return list(s)

def get_profile_class():
    """Gets the class to be used for user profiles"""
    profile_string = getattr(settings, 'AUTH_PROFILE_MODULE', 'member.UserProfile')
    app_label, model = profile_string.split('.')
    return models.get_model(app_label, model)

def parse_signed_data(signed_request, secret=None):
    """Parse a ``signed_request`` from Facebook.
    
    Thanks to http://stackoverflow.com/questions/3302946/how-to-base64-url-decode-in-python
    and http://sunilarora.org/parsing-signedrequest-parameter-in-python-bas
    
    :param signed_request: The signed request to be verified.
        This is a string containing two dot-separated parts: signature
        and data. Each part is (PHP-style) base64-encoded.
        Signature is a HMAC-SHA256 signature of the data, using APP_SECRET
        as the key. Data is a JSON-encoded object.
    :param secret: The key to be used to verify signature.
        Defaults to ``FACEBOOK_APP_SECRET`` from settings.
    :returns: The decoded data object if signature is valid, else ``None``.
    """
    
    if secret is None:
        secret = fb_settings.FACEBOOK_APP_SECRET
    
    enc_signature, enc_payload = signed_request.split('.', 1)
    signature, payload = map(urlsafer_b64decode, (enc_signature, enc_payload))
    data = json.loads(payload)
    algo = data.get('algorithm').upper()
    
    try:
        if verify_signature(enc_payload, secret, signature, algo):
            logger.debug("Received a valid signed request")
            return data
        else:
            logger.error("Invalid signed_data signature!")
            return
    except:
        logger.exception("Something went wrong while verifying the signed_request.")

def calculate_signature(data, secret, algorithm=None):
    """Calculate the signature of ``data`` using ``secret`` as key
    and the specified ``algorithm``.
    
    :param data: The data to be signed
    :param secret: The secret shared key
    :param algorithm: The algorithm to be used. Defaults to ``HMAC-SHA256``.
        Must be one of algorithms supported by hashlib, or an equivalent
        calllable / function.
    """
    import hmac, hashlib
    
    if algorithm is None:
        algorithm = 'HMAC-SHA256'

    if isinstance(algorithm, basestring):
        if algorithm == 'HMAC-SHA256':
            digestmod = hashlib.sha256
        elif algorithm == 'HMAC-MD5':
            digestmod = hashlib.md5
        elif algorithm == 'HMAC-SHA1':
            digestmod = hashlib.sha1
        elif algorithm == 'HMAC-SHA224':
            digestmod = hashlib.sha224
        elif algorithm == 'HMAC-SHA384':
            digestmod = hashlib.sha384
        elif algorithm == 'HMAC-SHA512':
            digestmod = hashlib.sha512
        else:
            raise ValueError("Unsupported algorithm: %r" % algorithm)
    else:
        ## Try using algorithm directly
        digestmod = algorithm
    return hmac.new(secret, msg=data, digestmod=digestmod).digest()

def verify_signature(data, secret, signature, algorithm=None):
    """Verify the ``signature`` on ``data`` using ``secret`` key."""
    _c_sig = calculate_signature(data, secret, algorithm)
    return signature == _c_sig

def to_int(s, default=0, exception=(ValueError, TypeError), regexp=None):
    '''Convert the given input to an integer or return default

    When trying to convert the exceptions given in the exception parameter
    are automatically catched and the default will be returned.

    The regexp parameter allows for a regular expression to find the digits
    in a string.
    When True it will automatically match any digit in the string.
    When a (regexp) object (has a search method) is given, that will be used.
    WHen a string is given, re.compile will be run over it first

    The last group of the regexp will be used as value
    '''
    if regexp is True:
        regexp = re.compile('(\d+)')
    elif isinstance(regexp, basestring):
        regexp = re.compile(regexp)
    elif hasattr(regexp, 'search'):
        pass
    elif regexp is not None:
        raise(TypeError, 'unknown argument for regexp parameter')

    try:
        if regexp:
            match = regexp.search(s)
            if match:
                s = match.groups()[-1]
        return int(s)
    except exception:
        return default

def encode_params(params_dict):
    """Take the dictionary of parameters and encode keys and
    values from unicode to ASCII.
    """
    encoded = [(smart_str(k), smart_str(v)) for k, v in params_dict.items()]
    encoded_dict = dict(encoded)
    return encoded_dict


def smart_str(s, encoding='utf-8', strings_only=False, errors='strict'):
    """Adapted from django, needed for urlencoding
    Returns a bytestring version of 's', encoded as specified in 'encoding'.
    If strings_only is True, don't convert (some) non-string-like objects.
    """
    import types
    if strings_only and isinstance(s, (types.NoneType, int)):
        return s
    elif not isinstance(s, basestring):
        try:
            return str(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                ## An Exception subclass containing non-ASCII data that
                ## doesn't know how to print itself properly.
                ## We shouldn't raise a further exception.
                return ' '.join([smart_str(arg, encoding, strings_only,
                        errors) for arg in s])
            return unicode(s).encode(encoding, errors)
    elif isinstance(s, unicode):
        return s.encode(encoding, errors)
    elif s and encoding != 'utf-8':
        return s.decode('utf-8', errors).encode(encoding, errors)
    else:
        return s

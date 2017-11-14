# coding=utf-8
"""
oauthlib_extras.oauth2.errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Error used both by OAuth 2 clients and providers to represent the spec
defined error responses for all four core grant types.
"""
from oauthlib.oauth2.rfc6749.errors import OAuth2Error


class MalformedResponseSecretError(OAuth2Error):
    error = 'malformed_response_secret'

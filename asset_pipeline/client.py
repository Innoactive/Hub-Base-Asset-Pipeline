import os
import time
from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
from requests_oauthlib import OAuth2Session

# needed for insecure http communication
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class ClientCredentialsOAuth2Session(OAuth2Session):
    """
    Simplified OAuth2Session for use with client-credentials grant type.
    Automatically grants new token, if request fails.
    """
    def __init__(self, token_url, client_id, client_secret, **kwargs):
        # http://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#backend-application-flow
        client = BackendApplicationClient(client_id=client_id)
        print 'Got in right constructor'
        super(ClientCredentialsOAuth2Session, self).__init__(client=client, **kwargs)
        # let's save the variables for later use
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        # assures we get initial access token
        self.get_valid_access_token()

    def request(self, *args, **kwargs):
        try:
            return super(ClientCredentialsOAuth2Session, self).request(*args, **kwargs)
        except TokenExpiredError:
            # the token expired, so we fetch a new one
            # there is no refresh for the client-credentials grant type
            self.fetch_token(self.token_url, client_id=self.client_id, client_secret=self.client_secret)
            # we got a new token, so let's retry the request
            return super(ClientCredentialsOAuth2Session, self).request(*args, **kwargs)

    def get_valid_access_token(self):
        if self.is_token_invalid():
            # token expired, so fetch a new one
            self.fetch_token(self.token_url, client_id=self.client_id, client_secret=self.client_secret)
        # return the valid access_token
        return self.access_token

    def is_token_invalid(self):
        # checks if token has already expired
        return not self._client._expires_at or self._client._expires_at < time.time()

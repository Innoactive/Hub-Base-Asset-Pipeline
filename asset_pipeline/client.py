import os
import sys
import pickle
import urllib

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from logger import logger
from oauthlib_extras.oauth2 import MailApplicationClient

# needed for insecure oauthlib http communication
# oauth2 is, as per specification, only allowed in
# combination with secure https communication
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

APPLICATION_STATE_FILE = 'state'


class ClientConfigParser():
    def __init__(self, config):
        self.config = config
        self.protocol = config.get('protocol', None) or 'http'
        self.host = config.get('host')
        self.port = config.get('port')
        self.ssl = config.get('ssl')
        # only if we didn't specify protocol explicitly
        if self.ssl and not config.get('protocpl'):
            self.protocol += 's'
        self.base_url = '{protocol}://{host}:{port}/'.format(protocol=self.protocol, host=self.host, port=self.port)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.oauth_code = config.get('oauth_code')
        self.username = config.get('username')
        self.password = config.get('password')
        self.email = config.get('email')
        if os.path.isfile(APPLICATION_STATE_FILE):
            with open(APPLICATION_STATE_FILE) as f:
                self.state = pickle.load(f).get('state', None)
        else:
            self.state = None
        self.validate_config()

    def validate_config(self):
        if not self.client_id or not self.client_secret:
            logger.info(
                'You must create an oauth client in the hub backend, and provide the client_id and client_secret'
                'in the config !')
            sys.exit(1)
        if not self.email and not self.username and not self.password:
            logger.info('Provide an email for the user you want to use the session with, or the username together with '
                        'the password (more insecure).')
            sys.exit(1)
        if not self.oauth_code and (not self.username or not self.password):
            logger.info('You must either provide the oauth_code, which you can get sent to you via mail, by visiting '
                        'the following url:')
            logger.info(self.get_authorization_url())
            logger.info('or, the more insecure option, you can provide an username and password (for an hub user) in '
                        'the config.')
            sys.exit(1)
        if self.oauth_code and not self.state:
            logger.info('You used some url for getting the oauth_code, not provided by this instance !')
            logger.info('Please only use the following url for your next secret grant:')
            logger.info(self.get_authorization_url())
            logger.info('Note, that the url changes !')
            sys.exit(1)

    def get_authorization_url(self):
        client_factory = ClientFactory(**self.get_factory_kwargs())
        auth_url, state = client_factory.get_authorization_url_and_state()
        state_file = {
            'state': state
        }
        with open(APPLICATION_STATE_FILE, 'w') as f:
            pickle.dump(state_file, f)
        return auth_url

    def get_factory_kwargs(self):
        kwargs = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'oauth_code': self.oauth_code,
            'username': self.username,
            'password': self.password,
            'base_url': self.base_url,
            'email': self.email
        }
        return kwargs


class ClientFactory():
    """
    Client factory, which creates the right oauth client, depending
    on the passed kwargs to the constructor.

    If the kwargs contain a value for the oauth_code and email,
    it will construct a mail application client (authorization
    code grant), otherwise it wil construct a legacy application
    client (password grant).
    """
    RELATIVE_OAUTH_TOKEN_URL = 'oauth/token/'
    RELATIVE_OAUTH_AUTHORIZATION_URL = 'oauth/authorize/'

    def __init__(self, client_id=None, client_secret=None, base_url=None, oauth_code=None, username=None,
                 password=None, state=None, email=None, pre_fetch_token=None, rel_token_url=None, rel_auth_url=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.oauth_code = oauth_code
        self.username = username
        self.password = password
        self.state = state
        self.email = email
        self.pre_fetch_token = pre_fetch_token
        self.token_url = urllib.basejoin(self.base_url, (rel_token_url or self.RELATIVE_OAUTH_TOKEN_URL))
        self.authorization_base_url = urllib.basejoin(self.base_url, (rel_auth_url or
                                                                      self.RELATIVE_OAUTH_AUTHORIZATION_URL))

    @property
    def client(self):
        """
        decides which client to construct and return
        :return:
        """
        if self.oauth_code and self.email:
            client = self.get_mail_application_client()
        else:
            client = self.get_legacy_application_client()
        client = self.configure_client(client)
        return client

    def get_mail_application_client(self):
        """
        Constructs a MailApplicationClient (authorization code grant)
        :return:
        """
        client = MailApplicationClient(client_id=self.client_id, state=self.state)
        oauth = OAuth2Session(client=client)
        extra_kwargs = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            # instead of the redirect_uri, we use the email
            'email': self.email
        }
        if self.pre_fetch_token:
            self.pre_fetch_token(oauth)
        oauth.fetch_token(self.token_url, authorization_response=self.oauth_code, **extra_kwargs)
        # allows requests_oauthlib to auto refresh expired access tokens
        oauth.auto_refresh_url = self.token_url
        oauth.auto_refresh_kwargs = extra_kwargs
        return oauth

    def get_legacy_application_client(self):
        """
        Constructs a LegacyApplicationClient (password grant)
        :return:
        """
        client = LegacyApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        extra_kwargs = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        if self.pre_fetch_token:
            self.pre_fetch_token(oauth)
        oauth.fetch_token(self.token_url, username=self.username, password=self.password, **extra_kwargs)
        # allows requests_oauthlib to auto refresh expired access tokens
        oauth.auto_refresh_url = self.token_url
        oauth.auto_refresh_kwargs = extra_kwargs
        return oauth

    def get_authorization_url_and_state(self):
        """
        Constructs an authorization url, which the user can visit
        to get the oauth_code (code and state).
        :return:
        """
        client = MailApplicationClient(client_id=self.client_id, state=self.state)
        oauth = OAuth2Session(client=client)
        return oauth.authorization_url(self.authorization_base_url, email=self.email)

    def configure_client(self, client):
        """
        Configures the client, so it automatically
        refreshes the token (or fetches) on an
        UNAUTHORIZED response, and retries the
        request with the new token.
        :param client:
        :return:
        """
        # we need to backup the original request function
        request_func = client.request
        UNAUHTORIZED = 401

        username = self.username
        password = self.password

        def request(*args, **kwargs):
            # the first call on the original request function of the client
            # note: the original request function manages auto refresh if token time expired
            try:
                res = request_func(*args, **kwargs)
            except InvalidGrantError:
                # case when token time expired and requests_oauthlib's auto refresh didn't work
                # our only option is fetching token (works only for password grant)
                if isinstance(client._client, LegacyApplicationClient):
                    client.fetch_token(client.auto_refresh_url, username=username, password=password,
                                       **client.auto_refresh_kwargs)
                    res = request_func(*args, **kwargs)
                else:
                    raise
            if 'auth' in kwargs:
                # 1. Case:
                # The caller is refresh_token or fetch_token. If we didn't return here, we would end in an infinite loop
                # 2. Case:
                # The user specified some custom authentication, so it's not our responsibility to manage it
                return res
            if res.status_code == UNAUHTORIZED:
                # expire time valid, but we still got an unauthorized response
                try:
                    # we try to refresh the token
                    client.refresh_token(client.auto_refresh_url)
                except InvalidGrantError:
                    # The hub throws an InvalidGrantError if we can't refresh
                    if isinstance(client._client, LegacyApplicationClient):
                        # In case it's a password grant type client,
                        # we just fetch the token again
                        client.fetch_token(client.auto_refresh_url, username=username, password=password,
                                           **client.auto_refresh_kwargs)
                    else:
                        # It's a code grant application, no help here
                        # nothing can be done
                        raise
                # we probably get a new token, so retry
                res = request_func(*args, **kwargs)
            return res

        def token_updater(self):
            pass

        # we change the request function to our new modified version
        client.request = request
        # important, because if we don't specify it, requests_oauthlib raises exceptions to signal update of token
        client.token_updater = token_updater

        return client


def get_client_for_config(config, rel_token_url=None, rel_auth_url=None, pre_fetch_token=None, state=None):
    """
    Helper method, which parses the config and returns the
    right client.
    :param config:
    :param rel_token_url:
    :param rel_auth_url:
    :param pre_fetch_token: function which does something with the oauth session
    before fetching the token (if needed)
    :param state:
    :return:
    """
    client_config_parser = ClientConfigParser(config)
    client_factory = ClientFactory(pre_fetch_token=pre_fetch_token, rel_token_url=rel_token_url,
                                   rel_auth_url=rel_auth_url, state=state, **client_config_parser.get_factory_kwargs())
    return client_factory.client

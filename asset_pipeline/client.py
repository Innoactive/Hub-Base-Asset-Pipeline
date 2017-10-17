import os
import pickle
import urllib

from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session

from logger import logger
from oauthlib_extras.oauth2 import MailApplicationClient


# needed for insecure oauthlib http communication
# oauth2 is, as per specification, only allowed in
# combination with secure https communication
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

APPLICATION_STATE_FILE = 'state'

class ClientConfigParser():
    CONFIG_VALIDATION_ERROR_MSG = 'Config file couldn\'t be validated'

    def __init__(self, config):
        self.config = config
        self.protocol = 'http'
        self.host = config.get('host')
        self.port = config.get('port')
        self.ssl = config.get('ssl')
        if self.ssl:
            self.protocol += 's'
        self.base_url = '{protocol}://{host}:{port}/'.format(protocol=self.protocol, host=self.host, port=self.port)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.oauth_secret = config.get('oauth_secret')
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
            logger.error('You must create an oauth client in the hub backend, and provide the client_id and client_secret'
                         'in the config !')
            raise AttributeError(self.CONFIG_VALIDATION_ERROR_MSG)
        if (not self.oauth_secret or not self.email) and (not self.username or not self.password):
            logger.error('You must either provide the oauth_secret together with the email of the user, which you can '
                         'get sent to you via mail, by visiting the following url:')
            logger.error(self.get_authorization_url())
            logger.error('or, the more insecure option, you can provide an username and password (for an hub user) in '
                         'the config.')
            raise AttributeError(self.CONFIG_VALIDATION_ERROR_MSG)
        if self.oauth_secret and not self.state:
            logger.error('You used some url for getting the oauth_secret, not provided by this instance !')
            logger.error('Please only use the following url for your next secret grant:')
            logger.error(self.get_authorization_url())
            logger.error('Note, that the url changes !')
            raise AttributeError(self.CONFIG_VALIDATION_ERROR_MSG)

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
            'oauth_secret': self.oauth_secret,
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

    If the kwargs contain a value for the oauth_secret and email,
    it will construct a mail application client (authorization
    code grant), otherwise it wil construct a legacy application
    client (password grant).
    """
    RELATIVE_OAUTH_TOKEN_URL = 'oauth/token/'
    RELATIVE_OAUTH_AUTHORIZATION_URL = 'oauth/authorize/'

    def __init__(self, client_id=None, client_secret=None, base_url=None, oauth_secret=None, username=None,
                 password=None, state=None, email=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.oauth_secret = oauth_secret
        self.username = username
        self.password = password
        self.state = state
        self.email = email
        self.token_url = urllib.basejoin(self.base_url, self.RELATIVE_OAUTH_TOKEN_URL)
        self.authorization_base_url = urllib.basejoin(self.base_url, self.RELATIVE_OAUTH_AUTHORIZATION_URL)

    @property
    def client(self):
        """
        decides which client to construct and return
        :return:
        """
        if self.oauth_secret and self.email:
            return self.get_mail_application_client()
        else:
            return self.get_legacy_application_client()

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
        oauth.fetch_token(self.token_url, authorization_response=self.oauth_secret, **extra_kwargs)
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
        oauth.fetch_token(self.token_url, username=self.username, password=self.password, **extra_kwargs)
        # allows requests_oauthlib to auto refresh expired access tokens
        oauth.auto_refresh_url = self.token_url
        oauth.auto_refresh_kwargs = extra_kwargs
        return oauth

    def get_authorization_url_and_state(self):
        """
        Constructs an authorization url, which the user can visit
        to get the oauth_secret (code and state).
        :return:
        """
        client = MailApplicationClient(client_id=self.client_id, state=self.state)
        oauth = OAuth2Session(client=client)
        return oauth.authorization_url(self.authorization_base_url)


def get_client_for_config(config):
    """
    Helper method, which parses the config and returns the
    right client.
    :param config:
    :return:
    """
    client_config_parser = ClientConfigParser(config)
    client_factory = ClientFactory(**client_config_parser.get_factory_kwargs())
    return client_factory.client

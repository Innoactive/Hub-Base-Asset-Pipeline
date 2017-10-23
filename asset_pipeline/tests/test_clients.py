import json
from enum import Enum
from collections import OrderedDict
from urlparse import urljoin, parse_qs
from unittest import TestCase

import requests
import requests_mock
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from ..client import get_client_for_config


HOST = 'sever.test'
PROTOCOL = 'http'
PORT = 80
BASE_URL = '{protocol}://{host}:{port}'.format(protocol=PROTOCOL, host=HOST, port=PORT)
AUTH_RELATIVE_URL = '/oauth/authorize/'
TOKEN_RELATIVE_URL = '/oauth/token/'
RESPONSE = 'myresponse'
MOCK_ENDPOINT = '/mock/'
TOKEN_TYPE = 'Bearer'
ACCESS_TOKEN = 'myaccesstoken'
REFRESH_TOKEN = 'myrefreshtoken'
AUTH_CODE = 'mycode'
STATE = 'mystate'
PASSWORD_GRANT = 'password'
CODE_GRANT = 'authorization_code'
REFRESH_GRANT = 'refresh_token'

TOKEN = {
    'token_type': TOKEN_TYPE,
    'access_token': ACCESS_TOKEN,
    'expires_in': 3600,
    'refresh_token': REFRESH_TOKEN
}

class Error(Enum):
    """
    OAuth Server Errors
    """
    INVALID_ACCESS_TOKEN = 1
    INVALID_REFRESH_TOKEN = 2

OAUTH_ERROR_MESSAGES = {
    # error status codes and responses for the mock oauth server
    # same messages for invalid and expired in the hub
    Error.INVALID_ACCESS_TOKEN: (401, '{"detail": "Authentication credentials were not provided."}'),
    Error.INVALID_REFRESH_TOKEN: (401, '{"error": "invalid_grant"}')
}

def get_response(content, request, status_code=200, is_json=False):
    """
    Helper function to construct a requests response
    :param content:
    :param request:
    :param status_code:
    :param is_json:
    :return:
    """
    response = requests.Response()
    response.status_code = status_code
    response.request = request
    response._content = json.dumps(content) if is_json else content
    return response

def get_data(body):
    """
    Helper function to get the POST data of a 'prepared request'
    :param body:
    :return:
    """
    data = parse_qs(body)
    for key, value in data.items():
        data[key] = value[0]
    return data

def match_token_request(request):
    """
    https://requests-mock.readthedocs.io/en/latest/matching.html#custom-matching
    Mock oauth token endpoint
    :param request:
    :return:
    """
    if request.path_url == TOKEN_RELATIVE_URL:
        if request.method == 'POST':
            data = get_data(request.body)
            print data
            grant_type = data.get('grant_type', None)
            if grant_type == PASSWORD_GRANT or grant_type == CODE_GRANT:
                if 'client_id' in data and 'client_secret' in data:
                    if ('username' in data and 'password' in data) or ('email' in data and 'code' in data):
                        # valid password or code grant, just return the token
                        return get_response(TOKEN, request, is_json=True)
            elif grant_type == REFRESH_GRANT:
                refresh_token = data.get('refresh_token', None)
                if refresh_token and refresh_token == REFRESH_TOKEN:
                    # grant using valid refresh token
                    return get_response(TOKEN, request, is_json=True)
                else:
                    # invalid refresh token
                    return get_response(OAUTH_ERROR_MESSAGES[Error.INVALID_REFRESH_TOKEN][1], request,
                                        status_code=OAUTH_ERROR_MESSAGES[Error.INVALID_REFRESH_TOKEN][0])

def match_mock_endpoint(request):
    """
    Dumb mock endpoint, which should return the RESPONSE.
    Checks for valid access_token.
    :param request:
    :return:
    """
    if request.path_url == MOCK_ENDPOINT:
        if request.method == 'GET':
            auth_header = request.headers.get('Authorization', None)
            if auth_header:
                if auth_header == '{token_type} {access_token}'.format(token_type=TOKEN_TYPE, access_token=ACCESS_TOKEN):
                    # valid access token, return the response
                    return get_response(RESPONSE, request)
                else:
                    # return error message
                    return get_response(OAUTH_ERROR_MESSAGES[Error.INVALID_ACCESS_TOKEN][1], request,
                                        status_code=OAUTH_ERROR_MESSAGES[Error.INVALID_ACCESS_TOKEN][0])


class OAuthMockServer(TestCase):
    """
    Base for oauth tests
    """
    def setUp(self):
        self.adapter = requests_mock.Adapter()
        self.adapter.add_matcher(match_token_request)
        # mock endpoint for testing authentication
        self.adapter.add_matcher(match_mock_endpoint)


class TestClient(OAuthMockServer):
    def setUp(self):
        # setup oauth mock endpoints
        super(TestClient, self).setUp()

        # setup configs
        common_config = {
            'host': HOST,
            'port': PORT,
            'protocol': PROTOCOL,
            'ssl': False,
            'client_id': 'myclient',
            'client_secret': 'mysecret'
        }

        legacy_config = common_config.copy()
        legacy_config['username'] = 'myuser'
        legacy_config['password'] = 'mypass'

        mail_config = common_config.copy()
        mail_config['email'] = 'myuser@server.test'
        mail_config['oauth_secret'] = '{code}&{state}'.format(code=AUTH_CODE, state=STATE)

        def pre_fetch_token_function(client):
            # remove standard http and https adapters
            client.adapters = OrderedDict()
            # mount mock adapter
            client.mount(PROTOCOL, self.adapter)

        common_kwargs = {
            # hook which get's called before fetch_token
            'pre_fetch_token': pre_fetch_token_function,
            'rel_auth_url': AUTH_RELATIVE_URL,
            'rel_token_url': TOKEN_RELATIVE_URL
        }
        # password grant client
        self.legacy_client = get_client_for_config(legacy_config, **common_kwargs)
        # code grant client
        self.mail_client = get_client_for_config(mail_config, state=STATE, **common_kwargs)

    def test_legacy_client(self):
        """
        Tests password grant client using valid token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        response = self.legacy_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_legacy_client_invalid_access_token(self):
        """
        Tests password grant client using invalid access_token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.legacy_client._client.access_token = 'invalidaccesstoken'
        response = self.legacy_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_legacy_client_expired_access_token(self):
        """
        Tests password grant client using expired access token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.legacy_client._client._expires_at = 1
        response = self.legacy_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_legacy_client_invalid_refresh_token(self):
        """
        Tests password grant client using invalid access token and invalid refresh token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.legacy_client._client.access_token = 'invalidaccesstoken'
        self.legacy_client.token['refresh_token'] = 'invalidrefreshtoken'
        response = self.legacy_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_legacy_client_invalid_refresh_token_expired_access_token(self):
        """
        Tests password grant client using expired access token and invalid refresh token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.legacy_client._client._expires_at = 1
        self.legacy_client.token['refresh_token'] = 'invalidrefreshtoken'
        response = self.legacy_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_mail_client(self):
        """
        Tests code grant client using valid token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        response = self.mail_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_mail_client_invalid_access_token(self):
        """
        Tests code grant client using invalid access_token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.mail_client._client.access_token = 'invalidaccesstoken'
        response = self.mail_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_mail_client_expired_access_token(self):
        """
        Tests code grant client using expired access token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.mail_client._client._expires_at = 1
        response = self.mail_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))
        self.assertEquals(response.content, RESPONSE)

    def test_mail_client_invalid_refresh_token(self):
        """
        Tests code grant client using invalid access token and invalid refresh token.
        Should get the value of the RESPONSE variable as response.
        :return:
        """
        self.mail_client._client.access_token = 'invalidaccesstoken'
        self.mail_client.token['refresh_token'] = 'invalidrefreshtoken'
        with self.assertRaises(InvalidGrantError):
            self.mail_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))

    def test_mail_client_invalid_refresh_token_expired_access_token(self):
        """
        Tests code grant client using expired access token and invalid refresh token.
        Should raise an InvalidGrantError.
        :return:
        """
        self.mail_client._client._expires_at = 1
        self.mail_client.token['refresh_token'] = 'invalidrefreshtoken'
        with self.assertRaises(InvalidGrantError):
            self.mail_client.request('GET', urljoin(BASE_URL, MOCK_ENDPOINT))

import requests
import textwrap

from mindsdb.utilities.config import Config


def get_aws_meta_data() -> dict:
    ''' returns aws metadata for current instance

        Returns:
            dict: aws metadata
    '''
    aws_meta_data = {
        'public-hostname': None,
        'ami-id': None,
        'instance-id': None
    }
    for key in aws_meta_data.keys():
        resp = requests.get(
            f'http://169.254.169.254/latest/meta-data/{key}',
            timeout=1
        )
        if resp.status_code != 200:
            raise Exception()
        aws_meta_data[key] = resp.text
    return aws_meta_data


def register_oauth_client():
    ''' register new oauth client if it is not existed
    '''
    config = Config()
    aws_meta_data = get_aws_meta_data()

    current_aws_meta_data = config.get('aws_meta_data', {})
    oauth_meta = config.get('auth', {}).get('oauth', {})

    public_hostname = aws_meta_data['public-hostname']
    if (
        current_aws_meta_data.get('public-hostname') != public_hostname
        or oauth_meta.get('client_id') is None
    ):
        resp = requests.post(
            f'https://{oauth_meta["server_host"]}/auth/register_client',
            json={
                'client_name': f'aws_marketplace_{public_hostname}',
                'client_uri': public_hostname,
                'grant_types': 'authorization_code',
                'redirect_uris': textwrap.dedent(f'''
                    https://{public_hostname}/api/auth/callback
                    https://{public_hostname}/api/auth/callback/cloud_home
                '''),
                'response_types': 'code',
                'scope': 'openid profile aws_marketplace',
                'token_endpoint_auth_method': 'client_secret_basic'
            },
            timeout=10
        )

        if resp.status_code != 200:
            raise Exception(f'Wrong answer from auth server: {resp.status_code}, {resp.text}')
        keys = resp.json()
        Config().update({
            'aws_meta_data': aws_meta_data,
            'auth': {
                'oauth': {
                    'client_id': keys['client_id'],
                    'client_secret': keys['client_secret']
                }
            }
        })

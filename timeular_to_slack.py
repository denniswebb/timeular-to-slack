from apiclient import APIClient, JsonRequestFormatter, JsonResponseHandler, HeaderAuthentication
import json, logging, os

TIMEULAR_ACTIVITY_TO_SLACK_STATUS = {
    'default': {
        'status': '',
        'emoji': ':smile:'
    },
    'Working': {
        'status': 'Focused Work',
        'emoji': ':thinking_face:'
    },
    'Meeting': {
        'status': 'In a meeting',
        'emoji': ':calendar:'
    }
}

class TimeularClient(APIClient):
    _api_key = None
    _api_secret = None
    _api_token = None
    _base_url = None

    def __init__(self, base_url='https://api.timeular.com/api/v2', api_key='', api_secret=''):
        super(TimeularClient, self).__init__(request_formatter=JsonRequestFormatter, response_handler=JsonResponseHandler)
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url
        get_access_token_result = self.get_access_token()
        self._api_token = get_access_token_result['token']
        self.set_authentication_method(authentication_method=HeaderAuthentication(token=self._api_token))

    def get_access_token(self):
        url = f"{self._base_url}/developer/sign-in"
        result = self.post(url, data={"apiKey": self._api_key, "apiSecret": self._api_secret})
        return result

    def get_tracking(self):
        url = f"{self._base_url}/tracking"
        result = self.get(url)
        return result

def main(event, context):
    config = {}
    config['TIMEULAR_API_KEY'] = os.environ.get('TIMEULAR_API_KEY')
    config['TIMEULAR_API_SECRET'] = os.environ.get('TIMEULAR_API_SECRET')
    config['SLACK_API_TOKEN'] = os.environ.get('SLACK_API_TOKEN')

    # very simple validation for expected env variables:
    for c in config:
        if config[c] is None:
            logging.error('Environment variable {} not found.'.format(c))
            return

    api = TimeularClient(api_key=config['TIMEULAR_API_KEY'], api_secret=config['TIMEULAR_API_SECRET'])

    current_activity = 'default'

    current_tracking = api.get_tracking()['currentTracking']

    if current_tracking:
        current_activity = current_tracking['activity']['name']



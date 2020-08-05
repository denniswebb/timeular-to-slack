from typing import Union

import aws_lambda_logging
import logging
import os

from apiclient import APIClient, JsonRequestFormatter, JsonResponseHandler, HeaderAuthentication
from slack import WebClient

TIMEULAR_ACTIVITY_TO_SLACK_STATUS = {
    'Working': {
        'text': 'Focused Work',
        'emoji': ':thinking_face:',
        'snooze': True
    },
    'Meeting': {
        'text': 'In a meeting',
        'emoji': ':calendar:',
        'snooze': True
    }
}


class TimeularClient(APIClient):
    _api_key: str = None
    _api_secret: str = None
    _api_token: str = None
    _base_url: str = None

    def __init__(self, base_url='https://api.timeular.com/api/v2', api_key='', api_secret=''):
        super(TimeularClient, self).__init__(request_formatter=JsonRequestFormatter,
                                             response_handler=JsonResponseHandler)
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url
        get_access_token_result = self.get_access_token()
        self._api_token = get_access_token_result['token']
        self.set_authentication_method(authentication_method=HeaderAuthentication(token=self._api_token))

    def get_access_token(self):
        url: str = f"{self._base_url}/developer/sign-in"
        result = self.post(url, data={"apiKey": self._api_key, "apiSecret": self._api_secret})
        return result

    def get_tracking(self):
        url: str = f"{self._base_url}/tracking"
        result = self.get(url)
        return result


def main(event, context):
    aws_lambda_logging.setup(
        level=os.getenv('DEBUG_LEVEL', 'WARN'),
        boto_level=os.getenv('DEBUG_BOTO_LEVEL', 'CRITICAL')
    )

    config = {'SLACK_API_TOKEN': os.environ.get('SLACK_API_TOKEN'),
              'SLACK_SNOOZE_DURATION': os.getenv('SLACK_SNOOZE_DURATION', '60'),
              'TIMEULAR_API_KEY': os.environ.get('TIMEULAR_API_KEY'),
              'TIMEULAR_API_SECRET': os.environ.get('TIMEULAR_API_SECRET')
              }

    for c in config:
        if config[c] is None:
            logging.error('Environment variable {} not found.'.format(c))
            return

    logging.debug("Initializing Timeular client")
    api = TimeularClient(api_key=config['TIMEULAR_API_KEY'], api_secret=config['TIMEULAR_API_SECRET'])

    logging.debug("Initializing Slack client")
    slack_client: WebClient = WebClient(token=config['SLACK_API_TOKEN'])

    logging.debug("Retrieving current Timeular tracking")
    current_tracking = api.get_tracking()['currentTracking']

    if current_tracking:
        current_activity = current_tracking['activity']['name']
        logging.debug(f"Timeular tracking activity {current_activity}")
    else:
        logging.debug("Timeular not tracking an activity")

    desired_slack_status = TIMEULAR_ACTIVITY_TO_SLACK_STATUS.get(
        current_activity,
        {
            'text': '',
            'emoji': '',
            'snooze': False
        }
    )
    desired_status_text: str = desired_slack_status['text']
    desired_status_emoji: str = desired_slack_status['emoji']
    desired_status_snooze: bool = desired_slack_status['snooze']

    current_slack_status = slack_client.users_profile_get()['profile']
    current_status_text: str = current_slack_status['status_text']

    logging.debug(f"Testing if \'{current_status_text}\' equals \'{desired_status_text}\'")
    if current_status_text == desired_status_text:
        logging.info("Status is already set. Exiting.")
        return

    logging.info(f"Setting Slack status to {desired_status_emoji} {desired_status_text}")
    slack_client.users_profile_set(profile={"status_text": desired_status_text, "status_emoji": desired_status_emoji})

    current_slack_snooze = slack_client.dnd_info()['snooze_enabled']
    if desired_status_snooze:
        if not current_slack_snooze:
            logging.info(f"Turning Slack snooze on for {config['SLACK_SNOOZE_DURATION']}")
            slack_client.dnd_setSnooze(num_minutes=int(config['SLACK_SNOOZE_DURATION']))
    else:
        if current_slack_snooze:
            logging.info("Turning Slack snooze off")
            slack_client.dnd_endSnooze()

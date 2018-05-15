import re

from app_integrations.apps.app_base import StreamAlertApp, AppIntegration

class SlackApp(AppIntegration):
    """SlackApp will audit 2 types of event logs: access logs and integration logs.

    This base class will be inherited by different subclasssed based on different
    event types.

    Access logs:
        contain information about logins

    Integration logs:
        contain details about your workspace's integrated apps
    """

    _SLACK_API_BASE_URL = 'https://slack.com/api/'

    @classmethod
    def _endpoint(cls):
        """Class method to return the endpoint to be used for this slack instance

        Returns:
            str: Path of the desired endpoint to query

        Raises:
            NotImplementedError: If the subclasses do not properly implement this method
        """
        raise NotImplementedError('Subclasses should implement the _endpoint method')

    def _process_log_payload(self, payload):
        raise NotImplementedError('Subclasses shouls implement the _process_log_payload method')

    @classmethod
    def _type(cls):
        raise NotImplementedError('Subclasses should implement the _type method')

    @classmethod
    def service(cls):
        return 'slack'

    @classmethod
    def date_formatter(cls):
        """Slack API date format: unix epoch seconds"""
        return '%s'

    @classmethod
    def _required_auth_info(cls):
        """Required credentials for access to the workspace"""
        return {
                'auth_token': {
                    'description': ('The security token generated by installing an app. '
                        'This should be a string of characters beginning with xoxp-'),
                    'format': re.compile(r'^xoxp-[a-zA-Z0-9-]+$')
                    }
                }

    def _gather_logs(self):
        """Gather log events.

        Returns:
            list: A list of dictionaries containing log events.
        """
        url = '{}{}'.format(self._SLACK_API_BASE_URL, self._endpoint())
        headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': 'Bearer {}'.format(self._config.auth['auth_token'])
                }
        success, response = self._make_post_request(
                url, headers, params, False)

        if not success:
            LOGGER.exception('Received bad response from slack')
            return False

        if not u'ok' in response.keys():
            LOGGER.exception('Received error or warning from slack')
            return False

        return _process_log_payload(response)


@StreamAlertApp
class SlackAccessApp(SlackApp):
    _SLACK_ACCESS_LOGS_ENDPOINT = 'team.accessLogs'

    @classmethod
    def _type(cls):
        return 'access'

    @classmethod
    def _endpoint(cls):
        return cls._SLACK_ACCESS_LOGS_ENDPOINT

    def _process_log_payload(self, payload):
        """Perform endpoint specific processing of the response to extract log events.

        Returns:
            list: a list of dictionaries containing log events
        """
        return [m for m in payload[u'login'] ] 

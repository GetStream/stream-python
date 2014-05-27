import requests
from stream import exceptions
import logging
from stream.signing import sign
from stream.utils import validate_feed

logger = logging.getLogger(__name__)


class StreamClient(object):
    base_url = 'https://getstream.io/api/'
    # base_url = 'http://localhost:8000/api/'

    def __init__(self, api_key, api_secret):
        '''
        Initialize the client with the given api key and secret

        :param api_key: the api key
        :param api_secret: the api secret

        **Example usage**::

            import stream
            # initialize the client
            client = stream.connect('key', 'secret')
            # get a feed object
            feed = client.feed('aggregated:1')
            # write data to the feed
            activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
            activity_id = feed.add_activity(activity_data)['id']
            activities = feed.get()

            feed.follow('flat:3')
            activities = feed.get()
            feed.unfollow('flat:3')
            feed.remove_activity(activity_id)
        '''
        self.api_key = api_key
        self.api_secret = api_secret

    def feed(self, feed_id):
        '''
        Returns a Feed object

        :param feed_id: the feed object
        '''
        validate_feed(feed_id)
        from stream.feed import Feed
        return Feed(self, feed_id)

    def get_default_params(self):
        '''
        Returns the params with the API key present
        '''
        params = dict(api_key=self.api_key)
        return params

    def get_headers(self, feed):
        '''
        Returns the headers with the signed authorization key
        '''
        feed = feed.replace(':', '')
        signature = sign(self.api_secret, feed)
        headers = {'Authorization': '%s %s' % (feed, signature)}
        return headers

    def _make_request(self, method, relative_url, feed, params=None, data=None):
        params = params or {}
        data = data or {}

        default_params = self.get_default_params()
        default_params.update(params)

        headers = self.get_headers(feed)
        url = self.base_url + relative_url

        logger.debug('stream api call %s, headers %s params %s data %s',
                     url, headers, default_params, data)
        response = method(url, data=data, headers=headers,
                          params=default_params)
        result = response.json()
        if result.get('exception'):
            self.raise_exception(result)
        return result

    def raise_exception(self, result):
        '''
        Map the exception code to an exception class and raise it
        '''
        from stream.exceptions import get_exception_dict
        error_message = result['detail']
        error_code = result.get('code')
        exception_dict = get_exception_dict()
        exception_class = exception_dict.get(
            error_code, exceptions.StreamApiException)
        exception = exception_class(error_message)
        raise exception

    def post(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(requests.post, *args, **kwargs)

    def get(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(requests.get, *args, **kwargs)

    def delete(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(requests.delete, *args, **kwargs)

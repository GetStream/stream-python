from requests.adapters import HTTPAdapter
from stream import exceptions, serializer
from stream.signing import sign
import logging
import os
import requests
from stream.utils import validate_feed_slug, validate_user_id


logger = logging.getLogger(__name__)


class StreamClient(object):
    base_url = 'https://api.getstream.io/api/'

    def __init__(self, api_key, api_secret, app_id, version='v1.0', timeout=3.0, base_url=None, location=None):
        '''
        Initialize the client with the given api key and secret

        :param api_key: the api key
        :param api_secret: the api secret
        :param app_id: the app id

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
        self.app_id = app_id
        self.version = version
        self.timeout = timeout
        self.location = location
        
        if base_url is not None:
            self.base_url = base_url
        elif location is not None:
            self.base_url = 'https://%s-api.getstream.io/api/' % location
        elif os.environ.get('LOCAL'):
            self.base_url = 'http://localhost:8000/api/'
            self.timeout = 20
            
        self.session = requests.Session()
        # TODO: turn this back on after we verify it doesnt retry on slower requests
        self.session.mount(self.base_url, HTTPAdapter(max_retries=0))

    def feed(self, feed_slug, user_id):
        '''
        Returns a Feed object

        :param feed_slug: the slug of the feed
        :param user_id: the user id
        '''
        from stream.feed import Feed
        feed_slug = validate_feed_slug(feed_slug)
        user_id = validate_user_id(user_id)

        # generate the token
        feed_id = '%s%s' % (feed_slug, user_id)
        token = sign(self.api_secret, feed_id)

        return Feed(self, feed_slug, user_id, token)

    def get_default_params(self):
        '''
        Returns the params with the API key present
        '''
        params = dict(api_key=self.api_key)
        return params

    def get_full_url(self, relative_url):
        url = self.base_url + self.version + '/' + relative_url
        return url

    def get_user_agent(self):
        from stream import __version__
        agent = 'stream-python-client-%s' % __version__
        return agent

    def _make_request(self, method, relative_url, signature, params=None, data=None):
        params = params or {}
        data = data or {}
        default_params = self.get_default_params()
        default_params.update(params)
        headers = {'Authorization': signature}
        headers['Content-type'] = 'application/json'
        headers['User-Agent'] = self.get_user_agent()
        url = self.get_full_url(relative_url)
        serialized = serializer.dumps(data)
        response = method(url, data=serialized, headers=headers,
                          params=default_params, timeout=self.timeout)
        logger.debug('stream api call %s, headers %s data %s',
                     response.url, headers, data)
        try:
            parsed_result = serializer.loads(response.text)
        except ValueError:
            parsed_result = None
        if parsed_result is None or parsed_result.get('exception') or response.status_code >= 500:
            self.raise_exception(parsed_result, status_code=response.status_code)
        return parsed_result

    def raise_exception(self, result, status_code):
        '''
        Map the exception code to an exception class and raise it
        If result.exception and result.detail are available use that
        Otherwise just raise a generic error
        '''
        from stream.exceptions import get_exception_dict
        exception_class = exceptions.StreamApiException
        
        if result is not None:
            error_message = result['detail']
            exception_fields = result.get('exception_fields')
            if exception_fields is not None:
                errors = []
                for field, errors in exception_fields.items():
                    errors.append('Field "%s" errors: %s' %
                                  (field, repr(errors)))
                error_message = '\n'.join(errors)
            error_code = result.get('code')
            exception_dict = get_exception_dict()
            exception_class = exception_dict.get(
                error_code, exceptions.StreamApiException)
        else:
            error_message = 'GetStreamAPI%s' % status_code
            
        exception = exception_class(error_message, status_code=status_code)
        raise exception

    def post(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(self.session.post, *args, **kwargs)

    def get(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(self.session.get, *args, **kwargs)

    def delete(self, *args, **kwargs):
        '''
        Shortcut for make request
        '''
        return self._make_request(self.session.delete, *args, **kwargs)

from datetime import datetime
import json
import logging
import os

import jwt
import requests
from stream.serializer import _datetime_encoder

from stream import exceptions, serializer
from stream.signing import sign
from stream.utils import validate_feed_slug, validate_user_id, validate_foreign_id_time
from stream.httpsig.requests_auth import HTTPSignatureAuth
from requests import Request

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

logger = logging.getLogger(__name__)


class StreamClient(object):

    def __init__(self, api_key, api_secret, app_id, version='v1.0', timeout=6.0, base_url=None, location=None):
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

        self.base_domain_name = 'stream-io-api.com'
        self.api_location = location
        self.custom_api_port = None
        self.protocol = 'https'

        if os.environ.get('LOCAL'):
            self.base_domain_name = 'localhost'
            self.protocol = 'http'
            self.custom_api_port = 8000
            self.timeout = 20
        elif base_url is not None:
            parsed_url = urlparse(base_url)
            self.base_domain_name = parsed_url.hostname
            self.protocol = parsed_url.scheme
            self.custom_api_port = parsed_url.port
            self.api_location = ""
        elif location is not None:
            self.location = location

        self.base_analytics_url = 'https://analytics.stream-io-api.com/analytics/'

        self.session = requests.Session()
        self.auth = HTTPSignatureAuth(api_key, secret=api_secret)
        
        # setup personalization
        from stream.personalization import Personalization
        token = self.create_jwt_token('personalization', '*', feed_id='*', user_id='*')
        self.personalization = Personalization(self, token)
        # setup the collection
        from stream.collections import Collections
        token = self.create_jwt_token('collections', '*', feed_id='*', user_id='*')
        self.collections = Collections(self, token)
        

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

    def get_default_header(self):
        base_headers = {
            'Content-type': 'application/json',
            'X-Stream-Client': self.get_user_agent()
        }
        return base_headers

    def get_full_url(self, service_name, relative_url):
        if self.api_location:
            hostname = '%s-%s.%s' % (self.api_location, service_name, self.base_domain_name)
        elif service_name:
            hostname = '%s.%s' % (service_name, self.base_domain_name)
        else:
            hostname = self.base_domain_name

        if self.base_domain_name == 'localhost':
            hostname = 'localhost'

        base_url = "%s://%s" % (self.protocol, hostname)

        if self.custom_api_port:
            base_url = "%s:%s" % (base_url, self.custom_api_port)

        url = base_url + '/' + service_name + '/' + self.version + '/' + relative_url
        return url

    def get_user_agent(self):
        from stream import __version__
        agent = 'stream-python-client-%s' % __version__
        return agent

    def _parse_response(self, response):
        try:
            parsed_result = serializer.loads(response.text)
        except ValueError:
            parsed_result = None
        if parsed_result is None or parsed_result.get('exception') or response.status_code >= 500:
            self.raise_exception(parsed_result, status_code=response.status_code)
        return parsed_result

    def _make_signed_request(self, method_name, relative_url, params=None, data=None):
        params = params or {}
        data = data or {}
        serialized = None
        headers = self.get_default_header()
        headers['X-Api-Key'] = self.api_key
        date_header = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        headers['Date'] = date_header
        default_params = self.get_default_params()
        default_params.update(params)
        url = self.get_full_url('api', relative_url)
        serialized = serializer.dumps(data)
        method = getattr(self.session, method_name)
        if method_name in ['post', 'put']:
            serialized = serializer.dumps(data)
        response = method(url, auth=self.auth, data=serialized, headers=headers,
                          params=default_params, timeout=self.timeout)
        logger.debug('stream api call %s, headers %s data %s',
                     response.url, headers, data)
        return self._parse_response(response)

    def create_jwt_token(self, resource, action, feed_id=None, user_id=None):
        '''
        Setup the payload for the given resource, action, feed or user
        and encode it using jwt
        '''
        payload = {
            'action': action,
            'resource': resource
        }
        if feed_id is not None:
            payload['feed_id'] = feed_id
        if user_id is not None:
            payload['user_id'] = user_id
        return jwt.encode(payload, self.api_secret).decode("utf-8")

    def _make_request(self, method, relative_url, signature, service_name='api', params=None, data=None):
        params = params or {}
        data = data or {}
        serialized = None
        default_params = self.get_default_params()
        default_params.update(params)
        headers = self.get_default_header()
        headers['Authorization'] = signature
        headers['stream-auth-type'] = 'jwt'

        if not relative_url.endswith('/'):
            relative_url += '/'

        url = self.get_full_url(service_name, relative_url)
        
        if method.__name__ in ['post', 'put', 'delete']:
            serialized = serializer.dumps(data)
        response = method(url, data=serialized, headers=headers,
                          params=default_params, timeout=self.timeout)
        logger.debug('stream api call %s, headers %s data %s',
                     response.url, headers, data)
        return self._parse_response(response)

    def raise_exception(self, result, status_code):
        '''
        Map the exception code to an exception class and raise it
        If result.exception and result.detail are available use that
        Otherwise just raise a generic error
        '''
        from stream.exceptions import get_exception_dict
        exception_class = exceptions.StreamApiException

        def errors_from_fields(exception_fields):
            result = []
            if not isinstance(exception_fields, dict):
                return exception_fields

            for field, errors in exception_fields.items():
                result.append('Field "%s" errors: %s' % (field, repr(errors)))
            return result

        if result is not None:
            error_message = result['detail']
            exception_fields = result.get('exception_fields')
            if exception_fields is not None:
                errors = []

                if isinstance(exception_fields, list):
                    errors = [errors_from_fields(exception_dict) for exception_dict in exception_fields]
                    errors = [item for sublist in errors for item in sublist]
                else:
                    errors = errors_from_fields(exception_fields)

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

    def add_to_many(self, activity, feeds):
        '''
        Adds an activity to many feeds

        :param activity: the activity data
        :param feeds: the list of follows (eg. ['feed:1', 'feed:2'])

        '''
        data = {'activity': activity, 'feeds': feeds}
        return self._make_signed_request('post', 'feed/add_to_many/', data=data)

    def follow_many(self, follows, activity_copy_limit=None):
        '''
        Creates many follows
        :param follows: the list of follow relations

        eg. [{'source': source, 'target': target}]

        '''
        params = None

        if activity_copy_limit != None:
            params = dict(activity_copy_limit=activity_copy_limit)

        return self._make_signed_request('post', 'follow_many/', params=params, data=follows)

    def update_activities(self, activities):
        '''
        Update or create activities
        '''
        if not isinstance(activities, (list, tuple, set)):
            raise TypeError('Activities parameter should be of type list')

        auth_token = self.create_jwt_token('activities', '*', feed_id='*')
        data = dict(activities=activities)
        return self.post('activities/', auth_token, data=data)

    def update_activity(self, activity):
        '''
        Update a single activity
        '''
        return self.update_activities([activity])

    def get_activities(self, ids=None, foreign_id_times=None):
        '''
        Retrieves activities by their ID or foreign_id + time combination

        ids: list of activity IDs
        foreign_id_time: list of tuples (foreign_id, time)
        '''
        auth_token = self.create_jwt_token('activities', '*', feed_id='*')

        if ids is None and foreign_id_times is None:
            raise TypeError('One the parameters ids or foreign_id_time must be provided and not None')

        if ids is not None and foreign_id_times is not None:
            raise TypeError('At most one of the parameters ids or foreign_id_time must be provided')

        query_params = {}

        if ids is not None:
            query_params['ids'] = ','.join(ids)

        if foreign_id_times is not None:
            validate_foreign_id_time(foreign_id_times)
            foreign_ids, timestamps = zip(*foreign_id_times)
            timestamps = map(_datetime_encoder, timestamps)
            query_params['foreign_ids'] = ','.join(foreign_ids)
            query_params['timestamps'] = ','.join(timestamps)

        return self.get('activities/', auth_token, params=query_params)

    def activity_partial_update(self, id=None, foreign_id=None, time=None, set={}, unset=[]):
        '''
        Partial update activity, via foreign ID or Foreign ID + timestamp

        id: the activity ID
        foreign_id: the activity foreign ID
        time: the activity time
        set: object containing the set operations
        unset: list of unset operations
        '''

        auth_token = self.create_jwt_token('activities', '*', feed_id='*')

        if id is None and (foreign_id is None or time is None):
            raise TypeError('The id or foreign_id+time parameters must be provided and not be None')
        if id is not None and (foreign_id is not None or time is not None):
            raise TypeError('Only one of the id or the foreign_id+time parameters can be provided')

        data = {
            'set': set,
            'unset': unset,
        }

        if id:
            data['id'] = id
        else:
            data['foreign_id'] = foreign_id
            data['time'] = time
        
        return self.post('activity/', auth_token, data=data)

    def create_redirect_url(self, target_url, user_id, events):
        '''
        Creates a redirect url for tracking the given events in the context
        of an email using Stream's analytics platform. Learn more at
        getstream.io/personalization
        '''
        # generate the JWT token
        auth_token = self.create_jwt_token('redirect_and_track', '*', '*', user_id=user_id)
        # setup the params
        params = dict(auth_type='jwt', authorization=auth_token, url=target_url)
        params['api_key'] = self.api_key
        params['events'] = json.dumps(events)
        url = self.base_analytics_url + 'redirect/'
        # we get the url from the prepare request, this skips issues with
        # python's urlencode implementation
        request = Request('GET', url, params=params)
        prepared_request = request.prepare()
        # validate the target url is valid
        Request('GET', target_url).prepare()
        return prepared_request.url

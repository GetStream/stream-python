import json
import os
from abc import ABC, abstractmethod

import requests

from stream import exceptions

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

import jwt


class AbstractStreamClient(ABC):
    @abstractmethod
    def feed(self, feed_slug, user_id):
        """
        Returns a Feed object

        :param feed_slug: the slug of the feed
        :param user_id: the user id
        """
        pass

    @abstractmethod
    def get_default_params(self):
        """
        Returns the params with the API key present
        """
        pass

    @abstractmethod
    def get_default_header(self):
        pass

    @abstractmethod
    def get_full_url(self, service_name, relative_url):
        pass

    @abstractmethod
    def get_user_agent(self):
        pass

    @abstractmethod
    def create_user_token(self, user_id, **extra_data):
        """
        Setup the payload for the given user_id with optional
        extra data (key, value pairs) and encode it using jwt
        """
        pass

    @abstractmethod
    def create_jwt_token(self, resource, action, feed_id=None, user_id=None, **params):
        """
        Set up the payload for the given resource, action, feed or user
        and encode it using jwt
        """
        pass

    @abstractmethod
    def raise_exception(self, result, status_code):
        """
        Map the exception code to an exception class and raise it
        If result.exception and result.detail are available use that
        Otherwise just raise a generic error
        """
        pass

    @abstractmethod
    def put(self, *args, **kwargs):
        """
        Shortcut for make request
        """
        pass

    @abstractmethod
    def post(self, *args, **kwargs):
        """
        Shortcut for make request
        """
        pass

    @abstractmethod
    def get(self, *args, **kwargs):
        """
        Shortcut for make request
        """
        pass

    @abstractmethod
    def delete(self, *args, **kwargs):
        """
        Shortcut for make request
        """
        pass

    @abstractmethod
    def add_to_many(self, activity, feeds):
        """
        Adds an activity to many feeds

        :param activity: the activity data
        :param feeds: the list of follows (eg. ['feed:1', 'feed:2'])

        """
        pass

    @abstractmethod
    def follow_many(self, follows, activity_copy_limit=None):
        """
        Creates many follows
        :param follows: the list of follow relations

        eg. [{'source': source, 'target': target}]

        """
        pass

    @abstractmethod
    def unfollow_many(self, unfollows):
        """
        Unfollows many feeds at batch
        :param unfollows: the list of unfollow relations

        eg. [{'source': source, 'target': target, 'keep_history': keep_history}]
        """
        pass

    @abstractmethod
    def update_activities(self, activities):
        """
        Update or create activities
        """
        pass

    @abstractmethod
    def update_activity(self, activity):
        """
        Update a single activity
        """
        pass

    @abstractmethod
    def get_activities(
        self, ids=None, foreign_id_times=None, enrich=False, reactions=None, **params
    ):
        """
        Retrieves activities by their ID or foreign_id + time combination

        Pass enrich and reactions options for enrichment

        ids: list of activity IDs
        foreign_id_time: list of tuples (foreign_id, time)
        """
        pass

    @abstractmethod
    def activity_partial_update(
        self, id=None, foreign_id=None, time=None, set=None, unset=None
    ):
        """
        Partial update activity, via activity ID or Foreign ID + timestamp

        id: the activity ID
        foreign_id: the activity foreign ID
        time: the activity time
        set: object containing the set operations
        unset: list of unset operations
        """
        pass

    @abstractmethod
    def activities_partial_update(self, updates=None):
        """
        Partial update activity, via activity ID or Foreign ID + timestamp

        :param updates: list of partial updates to perform.

        eg.
        [
            {
                "foreign_id": "post:1",
                "time": datetime.datetime.utcnow(),
                "set": {
                    "product.name": "boots",
                    "product.price": 7.99,
                    "popularity": 1000,
                    "foo": {"bar": {"baz": "qux"}},
                },
                "unset": ["product.color"]
            }
        ]
        """
        pass

    @abstractmethod
    def create_redirect_url(self, target_url, user_id, events):
        """
        Creates a redirect url for tracking the given events in the context
        of an email using Stream's analytics platform. Learn more at
        getstream.io/personalization
        """
        pass

    @abstractmethod
    def track_engagements(self, engagements):
        """
        Creates a list of engagements

        ;param engagements: Slice of engagements to create.

        eg.
        [
            {
                "content": "1",
                "label": "click",
                "features": [
                    {"group": "topic", "value": "js"},
                    {"group": "user", "value": "tommaso"},
                ],
                "user_data": "tommaso",
            },
            {
                "content": "2",
                "label": "click",
                "features": [
                    {"group": "topic", "value": "go"},
                    {"group": "user", "value": "tommaso"},
                ],
                "user_data": {"id": "486892", "alias": "Julian"},
            },
            {
                "content": "3",
                "label": "click",
                "features": [{"group": "topic", "value": "go"}],
                "user_data": {"id": "tommaso", "alias": "tommaso"},
            },
        ]
        """
        pass

    @abstractmethod
    def track_impressions(self, impressions):
        """
        Creates a list of impressions

        ;param impressions: Slice of impressions to create.

        eg.
        [
            {
                "content_list": ["1", "2", "3"],
                "features": [
                    {"group": "topic", "value": "js"},
                    {"group": "user", "value": "tommaso"},
                ],
                "user_data": {"id": "tommaso", "alias": "tommaso"},
            },
            {
                "content_list": ["2", "3", "5"],
                "features": [{"group": "topic", "value": "js"}],
                "user_data": {"id": "486892", "alias": "Julian"},
            },
        ]
        """
        pass

    @abstractmethod
    def og(self, target_url):
        """
        Retrieve open graph information from a URL which you can
        then use to add images and a description to activities.
        """
        pass

    @abstractmethod
    def follow_stats(self, feed_id, followers_slugs=None, following_slugs=None):
        """
        Retrieve the number of follower and following feed stats of a given feed.
        For each count, feed slugs can be provided to filter counts accordingly.

        eg.
        client.follow_stats(
        me, followers_slugs=['user'], following_slugs=['commodities']
        )
        this means to find counts of users following me and count
        of commodities I am following
        """
        pass

    @abstractmethod
    def _make_request(
        self,
        method,
        relative_url,
        signature,
        service_name="api",
        params=None,
        data=None,
    ):
        pass

    @abstractmethod
    def _parse_response(self, response):
        pass


class BaseStreamClient(AbstractStreamClient, ABC):
    """
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
    """

    def __init__(
        self,
        api_key,
        api_secret,
        app_id,
        version="v1.0",
        timeout=6.0,
        base_url=None,
        location=None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.app_id = app_id
        self.version = version
        self.timeout = timeout
        self.location = location
        self.base_domain_name = "stream-io-api.com"
        self.api_location = location
        self.custom_api_port = None
        self.protocol = "https"

        if os.environ.get("LOCAL"):
            self.base_domain_name = "localhost"
            self.protocol = "http"
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

        self.base_analytics_url = "https://analytics.stream-io-api.com/analytics/"

    def create_user_token(self, user_id, **extra_data):
        payload = {"user_id": user_id}
        for k, v in extra_data.items():
            payload[k] = v
        return jwt.encode(payload, self.api_secret, algorithm="HS256")

    def create_jwt_token(self, resource, action, feed_id=None, user_id=None, **params):
        payload = {**params, "action": action, "resource": resource}
        if feed_id is not None:
            payload["feed_id"] = feed_id
        if user_id is not None:
            payload["user_id"] = user_id
        return jwt.encode(payload, self.api_secret, algorithm="HS256")

    def raise_exception(self, result, status_code):
        from stream.exceptions import get_exception_dict

        exception_class = exceptions.StreamApiException

        def errors_from_fields(exception_fields):
            result = []
            if not isinstance(exception_fields, dict):
                return exception_fields

            for field, errors in exception_fields.items():
                result.append(f'Field "{field}" errors: {repr(errors)}')
            return result

        if result is not None:
            error_message = result["detail"]
            exception_fields = result.get("exception_fields")
            if exception_fields is not None:
                if isinstance(exception_fields, list):
                    errors = [
                        errors_from_fields(exception_dict)
                        for exception_dict in exception_fields
                    ]
                    errors = [item for sublist in errors for item in sublist]
                else:
                    errors = errors_from_fields(exception_fields)

                error_message = "\n".join(errors)
            error_code = result.get("code")
            exception_dict = get_exception_dict()
            exception_class = exception_dict.get(
                error_code, exceptions.StreamApiException
            )
        else:
            error_message = f"GetStreamAPI{status_code}"
        exception = exception_class(error_message, status_code=status_code)
        raise exception

    def create_redirect_url(self, target_url, user_id, events):
        # generate the JWT token
        auth_token = self.create_jwt_token(
            "redirect_and_track", "*", "*", user_id=user_id
        )
        # setup the params
        params = dict(auth_type="jwt", authorization=auth_token, url=target_url)
        params["api_key"] = self.api_key
        params["events"] = json.dumps(events)
        url = f"{self.base_analytics_url}redirect/"
        # we get the url from the prepare request, this skips issues with
        # python's urlencode implementation
        request = requests.Request("GET", url, params=params)
        prepared_request = request.prepare()
        # validate the target url is valid
        requests.Request("GET", target_url).prepare()
        return prepared_request.url

    def get_full_url(self, service_name, relative_url):
        if self.api_location:
            hostname = "{}{}.{}".format(
                self.api_location,
                "" if service_name == "analytics" else f"-{service_name}",
                self.base_domain_name,
            )
        elif service_name:
            hostname = f"{service_name}.{self.base_domain_name}"
        else:
            hostname = self.base_domain_name

        if self.base_domain_name == "localhost":
            hostname = "localhost"

        base_url = f"{self.protocol}://{hostname}"

        if self.custom_api_port:
            base_url = f"{base_url}:{self.custom_api_port}"

        url = base_url + "/" + service_name + "/" + self.version + "/" + relative_url
        return url

    def get_default_params(self):
        params = dict(api_key=self.api_key)
        return params

    def get_default_header(self):
        base_headers = {
            "Content-type": "application/json",
            "X-Stream-Client": self.get_user_agent(),
        }
        return base_headers

    def get_user_agent(self):
        from stream import __version__

        return f"stream-python-client-{__version__}"

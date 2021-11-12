import json
import logging

import requests
from requests import Request

from stream import serializer
from stream.client.base import BaseStreamClient
from stream.collections.collections import Collections
from stream.feed import Feed
from stream.personalization import Personalization
from stream.reactions import Reactions
from stream.serializer import _datetime_encoder
from stream.users import Users
from stream.utils import (
    get_reaction_params,
    validate_feed_slug,
    validate_foreign_id_time,
    validate_user_id,
)

try:
    from urllib.parse import urlparse
except ImportError:
    pass
    # from urlparse import urlparse

logger = logging.getLogger(__name__)


class StreamClient(BaseStreamClient):
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
        super().__init__(
            api_key,
            api_secret,
            app_id,
            version=version,
            timeout=timeout,
            base_url=base_url,
            location=location,
        )

        self.session = requests.Session()

        token = self.create_jwt_token("personalization", "*", feed_id="*", user_id="*")
        self.personalization = Personalization(self, token)

        token = self.create_jwt_token("collections", "*", feed_id="*", user_id="*")
        self.collections = Collections(self, token)

        token = self.create_jwt_token("reactions", "*", feed_id="*")
        self.reactions = Reactions(self, token)

        token = self.create_jwt_token("users", "*", feed_id="*")
        self.users = Users(self, token)

    def feed(self, feed_slug, user_id):
        feed_slug = validate_feed_slug(feed_slug)
        user_id = validate_user_id(user_id)
        token = self.create_jwt_token("feed", "*", feed_id="*")
        return Feed(self, feed_slug, user_id, token)

    def put(self, *args, **kwargs):
        return self._make_request(self.session.put, *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._make_request(self.session.post, *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._make_request(self.session.get, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._make_request(self.session.delete, *args, **kwargs)

    def add_to_many(self, activity, feeds):
        data = {"activity": activity, "feeds": feeds}
        token = self.create_jwt_token("feed", "*", feed_id="*")
        return self.post("feed/add_to_many/", token, data=data)

    def follow_many(self, follows, activity_copy_limit=None):
        params = None

        if activity_copy_limit is not None:
            params = dict(activity_copy_limit=activity_copy_limit)
        token = self.create_jwt_token("follower", "*", feed_id="*")
        return self.post("follow_many/", token, params=params, data=follows)

    def unfollow_many(self, unfollows):
        params = None

        token = self.create_jwt_token("follower", "*", feed_id="*")
        return self.post("unfollow_many/", token, params=params, data=unfollows)

    def update_activities(self, activities):
        if not isinstance(activities, (list, tuple, set)):
            raise TypeError("Activities parameter should be of type list")

        auth_token = self.create_jwt_token("activities", "*", feed_id="*")
        data = dict(activities=activities)
        return self.post("activities/", auth_token, data=data)

    def update_activity(self, activity):
        return self.update_activities([activity])

    def get_activities(
        self, ids=None, foreign_id_times=None, enrich=False, reactions=None, **params
    ):
        auth_token = self.create_jwt_token("activities", "*", feed_id="*")

        if ids is None and foreign_id_times is None:
            raise TypeError(
                "One the parameters ids or foreign_id_time must be provided and not None"
            )

        if ids is not None and foreign_id_times is not None:
            raise TypeError(
                "At most one of the parameters ids or foreign_id_time must be provided"
            )

        endpoint = "activities/"
        if enrich or reactions is not None:
            endpoint = "enrich/" + endpoint

        query_params = {**params}

        if ids is not None:
            query_params["ids"] = ",".join(ids)

        if foreign_id_times is not None:
            validate_foreign_id_time(foreign_id_times)
            foreign_ids, timestamps = zip(*foreign_id_times)
            timestamps = map(_datetime_encoder, timestamps)
            query_params["foreign_ids"] = ",".join(foreign_ids)
            query_params["timestamps"] = ",".join(timestamps)

        query_params.update(get_reaction_params(reactions))

        return self.get(endpoint, auth_token, params=query_params)

    def activity_partial_update(
        self, id=None, foreign_id=None, time=None, set=None, unset=None
    ):
        if id is None and (foreign_id is None or time is None):
            raise TypeError(
                "The id or foreign_id+time parameters must be provided and not be None"
            )
        if id is not None and (foreign_id is not None or time is not None):
            raise TypeError(
                "Only one of the id or the foreign_id+time parameters can be provided"
            )

        data = {"set": set or {}, "unset": unset or []}

        if id is not None:
            data["id"] = id
        else:
            data["foreign_id"] = foreign_id
            data["time"] = time

        return self.activities_partial_update(updates=[data])

    def activities_partial_update(self, updates=None):

        auth_token = self.create_jwt_token("activities", "*", feed_id="*")

        data = {"changes": updates or []}

        return self.post("activity/", auth_token, data=data)

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
        request = Request("GET", url, params=params)
        prepared_request = request.prepare()
        # validate the target url is valid
        Request("GET", target_url).prepare()
        return prepared_request.url

    def track_engagements(self, engagements):

        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        self.post(
            "engagement/",
            auth_token,
            data={"content_list": engagements},
            service_name="analytics",
        )

    def track_impressions(self, impressions):

        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        self.post("impression/", auth_token, data=impressions, service_name="analytics")

    def og(self, target_url):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        params = {"url": target_url}
        return self.get("og/", auth_token, params=params)

    def follow_stats(self, feed_id, followers_slugs=None, following_slugs=None):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        params = {
            "followers": feed_id,
            "following": feed_id,
        }

        if followers_slugs:
            params["followers_slugs"] = (
                ",".join(followers_slugs)
                if isinstance(followers_slugs, list)
                else followers_slugs
            )

        if following_slugs:
            params["following_slugs"] = (
                ",".join(following_slugs)
                if isinstance(following_slugs, list)
                else following_slugs
            )

        return self.get("stats/follow/", auth_token, params=params)

    def _make_request(
        self,
        method,
        relative_url,
        signature,
        service_name="api",
        params=None,
        data=None,
    ):
        params = params or {}
        data = data or {}
        serialized = None
        default_params = self.get_default_params()
        default_params.update(params)
        headers = self.get_default_header()
        headers["Authorization"] = signature
        headers["stream-auth-type"] = "jwt"

        if not relative_url.endswith("/"):
            relative_url += "/"

        url = self.get_full_url(service_name, relative_url)

        if method.__name__ in ["post", "put", "delete"]:
            serialized = serializer.dumps(data)
        response = method(
            url,
            data=serialized,
            headers=headers,
            params=default_params,
            timeout=self.timeout,
        )
        logger.debug(
            f"stream api call {response.url}, headers {headers} data {data}"
        )
        return self._parse_response(response)

    def _parse_response(self, response):
        try:
            parsed_result = serializer.loads(response.text)
        except ValueError:
            parsed_result = None
        if (
            parsed_result is None
            or parsed_result.get("exception")
            or response.status_code >= 500
        ):
            self.raise_exception(parsed_result, status_code=response.status_code)

        return parsed_result

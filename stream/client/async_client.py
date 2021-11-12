import logging

import aiohttp
from aiohttp import ClientConnectionError

from stream import serializer
from stream.client.base import BaseStreamClient
from stream.collections import AsyncCollections
from stream.feed.feeds import AsyncFeed
from stream.personalization import AsyncPersonalization
from stream.reactions import AsyncReactions
from stream.serializer import _datetime_encoder
from stream.users import AsyncUsers
from stream.utils import (
    get_reaction_params,
    validate_feed_slug,
    validate_foreign_id_time,
    validate_user_id,
)

logger = logging.getLogger(__name__)


class AsyncStreamClient(BaseStreamClient):
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
        self.session = aiohttp.ClientSession

        token = self.create_jwt_token("collections", "*", feed_id="*", user_id="*")
        self.collections = AsyncCollections(self, token)

        token = self.create_jwt_token("personalization", "*", feed_id="*", user_id="*")
        self.personalization = AsyncPersonalization(self, token)

        token = self.create_jwt_token("reactions", "*", feed_id="*")
        self.reactions = AsyncReactions(self, token)

        token = self.create_jwt_token("users", "*", feed_id="*")
        self.users = AsyncUsers(self, token)

    def feed(self, feed_slug, user_id):
        feed_slug = validate_feed_slug(feed_slug)
        user_id = validate_user_id(user_id)
        token = self.create_jwt_token("feed", "*", feed_id="*")
        return AsyncFeed(self, feed_slug, user_id, token)

    async def put(self, *args, **kwargs):
        return await self._make_request("PUT", *args, **kwargs)

    async def post(self, *args, **kwargs):
        return await self._make_request("POST", *args, **kwargs)

    async def get(self, *args, **kwargs):
        return await self._make_request("GET", *args, **kwargs)

    async def delete(self, *args, **kwargs):
        return await self._make_request("DELETE", *args, **kwargs)

    async def add_to_many(self, activity, feeds):
        data = {"activity": activity, "feeds": feeds}
        token = self.create_jwt_token("feed", "*", feed_id="*")
        return await self.post("feed/add_to_many/", token, data=data)

    async def follow_many(self, follows, activity_copy_limit=None):
        params = None

        if activity_copy_limit is not None:
            params = dict(activity_copy_limit=activity_copy_limit)
        token = self.create_jwt_token("follower", "*", feed_id="*")
        return await self.post("follow_many/", token, params=params, data=follows)

    async def unfollow_many(self, unfollows):
        params = None

        token = self.create_jwt_token("follower", "*", feed_id="*")
        return await self.post("unfollow_many/", token, params=params, data=unfollows)

    async def update_activities(self, activities):
        if not isinstance(activities, (list, tuple, set)):
            raise TypeError("Activities parameter should be of type list")

        auth_token = self.create_jwt_token("activities", "*", feed_id="*")
        data = dict(activities=activities)
        return await self.post("activities/", auth_token, data=data)

    async def update_activity(self, activity):
        return await self.update_activities([activity])

    async def get_activities(
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

        return await self.get(endpoint, auth_token, params=query_params)

    async def activity_partial_update(
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

        return await self.activities_partial_update(updates=[data])

    async def activities_partial_update(self, updates=None):
        auth_token = self.create_jwt_token("activities", "*", feed_id="*")

        data = {"changes": updates or []}

        return await self.post("activity/", auth_token, data=data)

    async def track_engagements(self, engagements):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        await self.post(
            "engagement/",
            auth_token,
            data={"content_list": engagements},
            service_name="analytics",
        )

    async def track_impressions(self, impressions):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        await self.post(
            "impression/", auth_token, data=impressions, service_name="analytics"
        )

    async def og(self, target_url):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        params = {"url": target_url}
        return await self.get("og/", auth_token, params=params)

    async def follow_stats(self, feed_id, followers_slugs=None, following_slugs=None):
        auth_token = self.create_jwt_token("*", "*", feed_id="*")
        params = {"followers": feed_id, "following": feed_id}

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

        return await self.get("stats/follow/", auth_token, params=params)

    async def _make_request(
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
        params = self._check_params(params)
        default_params.update(params)
        headers = self.get_default_header()
        headers["Authorization"] = signature
        headers["stream-auth-type"] = "jwt"

        if not relative_url.endswith("/"):
            relative_url += "/"

        url = self.get_full_url(service_name, relative_url)

        if method.lower() in ["post", "put", "delete"]:
            serialized = serializer.dumps(data)

        async with self.session() as session:
            async with session.request(
                method,
                url,
                data=serialized,
                headers=headers,
                params=default_params,
                timeout=self.timeout,
                verify_ssl=False,
            ) as response:

                logger.debug(
                    f"stream api call {response}, headers {headers} data {data}",
                )
                return await self._parse_response(response)

    async def _parse_response(self, response):
        try:
            parsed_result = serializer.loads(await response.text())
        except (ValueError, ClientConnectionError):
            parsed_result = None
        if (
            parsed_result is None
            or parsed_result.get("exception")
            or response.status >= 500
        ):
            self.raise_exception(parsed_result, status_code=response.status)

        return parsed_result

    def _check_params(self, params):
        """There is no standard for boolean representation of boolean values in YARL"""
        if not isinstance(params, dict):
            raise TypeError("Invalid params type")

        for key, value in params.items():
            if isinstance(value, bool):
                params[key] = str(value)

        return params

import copy
import datetime
import json
import os
import random
import sys
import time
from itertools import count
from uuid import uuid1, uuid4

import jwt
import pytz
import requests
from dateutil.tz import tzlocal
from requests.exceptions import MissingSchema

import stream
from stream import serializer
from stream.exceptions import ApiKeyException, InputException
from stream.feed import Feed

try:
    from unittest.case import TestCase
except ImportError:
    from unittest import TestCase


try:
    from urlparse import urlparse, parse_qs
except ImportError:
    from urllib.parse import urlparse, parse_qs


def connect_debug():
    try:
        key = os.environ["STREAM_KEY"]
        secret = os.environ["STREAM_SECRET"]
    except KeyError:
        print(
            "To run the tests the STREAM_KEY and STREAM_SECRET variables "
            "need to be available. \n"
            "Please create a pull request if you are an external "
            "contributor, because these variables are automatically added "
            "by Travis."
        )
        sys.exit(1)

    return stream.connect(key, secret, location="qa", timeout=30)


client = connect_debug()

counter = count()
test_identifier = uuid4()


def get_unique_postfix():
    return "---test_%s-feed_%s" % (test_identifier, next(counter))


def getfeed(feed_slug, user_id):
    """
    Adds the random postfix to the user id
    """
    return client.feed(feed_slug, user_id + get_unique_postfix())


def api_request_parse_validator(test):
    def wrapper(meth):
        def _parse_response(*args, **kwargs):
            response = meth(*args, **kwargs)
            test.assertTrue("duration" in response)
            return response

        return _parse_response

    return wrapper


class ClientTest(TestCase):
    def setUp(self):
        client._parse_response = api_request_parse_validator(self)(
            client._parse_response
        )

        # DEBUG account details
        user1 = getfeed("user", "1")
        user2 = getfeed("user", "2")
        aggregated2 = getfeed("aggregated", "2")
        aggregated3 = getfeed("aggregated", "3")
        topic1 = getfeed("topic", "1")
        flat3 = getfeed("flat", "3")

        self.c = client
        self.user1 = user1
        self.user2 = user2
        self.aggregated2 = aggregated2
        self.aggregated3 = aggregated3
        self.topic1 = topic1
        self.flat3 = flat3

        self.local_tests = False
        if "LOCAL" in os.environ:
            self.local_tests = os.environ["LOCAL"]

    def _test_sleep(self, production_wait, local_wait):
        """
        when testing against a live API, sometimes we need a small sleep to
        ensure data stability, however when testing locally the wait does
        not need to be as long
        :param production_wait: float, number of seconds to sleep when hitting real API
        :param local_wait: float, number of seconds to sleep when hitting localhost API
        :return: None
        """
        sleep_time = production_wait
        if self.local_tests:
            sleep_time = local_wait
        time.sleep(sleep_time)

    def test_collections_url(self):
        feed_url = client.get_full_url(relative_url="meta/", service_name="api")

        if self.local_tests:
            self.assertEqual(feed_url, "http://localhost:8000/api/v1.0/meta/")
        else:
            self.assertEqual(
                feed_url, "https://qa-api.stream-io-api.com/api/v1.0/meta/"
            )

    def test_analytics_url(self):
        feed_url = client.get_full_url(
            relative_url="engagement/", service_name="analytics"
        )

        if self.local_tests:
            self.assertEqual(
                feed_url, "http://localhost:8000/analytics/v1.0/engagement/"
            )
        else:
            self.assertEqual(
                feed_url, "https://qa.stream-io-api.com/analytics/v1.0/engagement/"
            )

    def test_personalization_url(self):
        feed_url = client.get_full_url(
            relative_url="recommended", service_name="personalization"
        )

        if self.local_tests:
            self.assertEqual(
                feed_url, "http://localhost:8000/personalization/v1.0/recommended"
            )
        else:
            self.assertEqual(
                feed_url,
                "https://qa-personalization.stream-io-api.com/personalization/v1.0/recommended",
            )

    def test_api_url(self):
        feed_url = client.get_full_url(service_name="api", relative_url="feed/")

        if self.local_tests:
            self.assertEqual(feed_url, "http://localhost:8000/api/v1.0/feed/")
        else:
            self.assertEqual(
                feed_url, "https://qa-api.stream-io-api.com/api/v1.0/feed/"
            )

    def test_collections_url_default(self):
        c = stream.connect("key", "secret")
        feed_url = c.get_full_url(relative_url="meta/", service_name="api")

        if not self.local_tests:
            self.assertEqual(feed_url, "https://api.stream-io-api.com/api/v1.0/meta/")

    def test_personalization_url_default(self):
        c = stream.connect("key", "secret")
        feed_url = c.get_full_url(
            relative_url="recommended", service_name="personalization"
        )

        if not self.local_tests:
            self.assertEqual(
                feed_url,
                "https://personalization.stream-io-api.com/personalization/v1.0/recommended",
            )

    def test_api_url_default(self):
        c = stream.connect("key", "secret")
        feed_url = c.get_full_url(service_name="api", relative_url="feed/")

        if not self.local_tests:
            self.assertEqual(feed_url, "https://api.stream-io-api.com/api/v1.0/feed/")

    def test_collections_url_location(self):
        c = stream.connect("key", "secret", location="tokyo")
        feed_url = c.get_full_url(relative_url="meta/", service_name="api")

        if not self.local_tests:
            self.assertEqual(
                feed_url, "https://tokyo-api.stream-io-api.com/api/v1.0/meta/"
            )

    def test_personalization_url_location(self):
        c = stream.connect("key", "secret", location="tokyo")
        feed_url = c.get_full_url(
            relative_url="recommended", service_name="personalization"
        )

        if not self.local_tests:
            self.assertEqual(
                feed_url,
                "https://tokyo-personalization.stream-io-api.com/personalization/v1.0/recommended",
            )

    def test_api_url_location(self):
        c = stream.connect("key", "secret", location="tokyo")
        feed_url = c.get_full_url(service_name="api", relative_url="feed/")

        if not self.local_tests:
            self.assertEqual(
                feed_url, "https://tokyo-api.stream-io-api.com/api/v1.0/feed/"
            )

    def test_update_activities_create(self):
        activities = [
            {
                "actor": "user:1",
                "verb": "do",
                "object": "object:1",
                "foreign_id": "object:1",
                "time": datetime.datetime.utcnow().isoformat(),
            }
        ]

        self.c.update_activities(activities)

    def test_update_activities_illegal_argument(self):
        activities = dict()

        def invalid_activities():
            self.c.update_activities(activities)

        self.assertRaises(TypeError, invalid_activities)

    def test_update_activities_update(self):
        activities = []
        for i in range(0, 10):
            activities.append(
                {
                    "actor": "user:1",
                    "verb": "do",
                    "object": "object:%s" % i,
                    "foreign_id": "object:%s" % i,
                    "time": datetime.datetime.utcnow().isoformat(),
                }
            )
        activities_created = self.user1.add_activities(activities)["activities"]
        activities = copy.deepcopy(activities_created)

        for activity in activities:
            activity.pop("id")
            activity["popularity"] = 100

        self.c.update_activities(activities)

        activities_updated = self.user1.get(limit=len(activities))["results"]
        activities_updated.reverse()

        for i, activity in enumerate(activities_updated):
            self.assertEqual(activities_created[i].get("id"), activity.get("id"))
            self.assertEqual(activity["popularity"], 100)

    def test_heroku(self):
        url = "https://thierry:pass@getstream.io/?app_id=1"
        os.environ["STREAM_URL"] = url
        c = stream.connect()
        self.assertEqual(c.api_key, "thierry")
        self.assertEqual(c.api_secret, "pass")
        self.assertEqual(c.app_id, "1")

    def test_heroku_no_location(self):
        url = "https://bvt88g4kvc63:twc5ywfste5bm2ngqkzs7ukxk3pn96yweghjrxcmcrarnt3j4dqj3tucbhym5wfd@stream-io-api.com/?app_id=669"
        os.environ["STREAM_URL"] = url
        c = stream.connect()
        self.assertEqual(c.api_key, "bvt88g4kvc63")
        self.assertEqual(
            c.api_secret,
            "twc5ywfste5bm2ngqkzs7ukxk3pn96yweghjrxcmcrarnt3j4dqj3tucbhym5wfd",
        )
        self.assertEqual(c.app_id, "669")
        feed_url = c.get_full_url("api", "feed/")

        if self.local_tests:
            self.assertEqual(feed_url, "http://localhost:8000/api/v1.0/feed/")
        else:
            self.assertEqual(feed_url, "https://api.stream-io-api.com/api/v1.0/feed/")

    def test_heroku_location_compat(self):
        url = "https://ahj2ndz7gsan:gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy@us-east.getstream.io/?app_id=1"
        os.environ["STREAM_URL"] = url
        c = stream.connect()
        self.assertEqual(c.api_key, "ahj2ndz7gsan")
        self.assertEqual(
            c.api_secret,
            "gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy",
        )

        feed_url = c.get_full_url("api", "feed/")
        if self.local_tests:
            self.assertEqual(feed_url, "http://localhost:8000/api/v1.0/feed/")
        else:
            self.assertEqual(
                feed_url, "https://us-east-api.stream-io-api.com/api/v1.0/feed/"
            )

        self.assertEqual(c.app_id, "1")

    def test_heroku_location(self):
        url = "https://ahj2ndz7gsan:gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy@us-east.stream-io-api.com/?app_id=1"
        os.environ["STREAM_URL"] = url
        c = stream.connect()
        self.assertEqual(c.api_key, "ahj2ndz7gsan")
        self.assertEqual(
            c.api_secret,
            "gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy",
        )

        feed_url = c.get_full_url("api", "feed/")
        if self.local_tests:
            self.assertEqual(feed_url, "http://localhost:8000/api/v1.0/feed/")
        else:
            self.assertEqual(
                feed_url, "https://us-east-api.stream-io-api.com/api/v1.0/feed/"
            )
        self.assertEqual(c.app_id, "1")

    def test_heroku_overwrite(self):
        url = "https://thierry:pass@getstream.io/?app_id=1"
        os.environ["STREAM_URL"] = url
        c = stream.connect("a", "b", "c")
        self.assertEqual(c.api_key, "a")
        self.assertEqual(c.api_secret, "b")
        self.assertEqual(c.app_id, "c")

    def test_location_support(self):
        c = stream.connect("a", "b", "c", location="us-east")

        full_location = "https://us-east-api.stream-io-api.com/api/v1.0/feed/"
        if self.local_tests:
            full_location = "http://localhost:8000/api/v1.0/feed/"

        self.assertEqual(c.location, "us-east")
        feed_url = c.get_full_url("api", "feed/")
        self.assertEqual(feed_url, full_location)

        # test a wrong location, can only work on non-local test running
        if not self.local_tests:
            c = stream.connect("a", "b", "c", location="nonexistant")

            def get_feed():
                c.feed("user", "1").get()

            self.assertRaises(requests.exceptions.ConnectionError, get_feed)

    def test_invalid_feed_values(self):
        def invalid_feed_slug():
            client.feed("user:", "1")

        self.assertRaises(ValueError, invalid_feed_slug)

        def invalid_user_id():
            client.feed("user:", "1-a")

        self.assertRaises(ValueError, invalid_user_id)

        def invalid_follow_feed_slug():
            self.user1.follow("user:", "1")

        self.assertRaises(ValueError, invalid_follow_feed_slug)

        def invalid_follow_user_id():
            self.user1.follow("user", "1-:a")

        self.assertRaises(ValueError, invalid_follow_user_id)

    def test_token_retrieval(self):
        _ = self.user1.token
        _ = self.user1.get_readonly_token()

    def test_user_token(self):
        token = self.c.create_user_token("user")
        payload = jwt.decode(token, self.c.api_secret, algorithms=["HS256"])
        self.assertEqual(payload["user_id"], "user")
        token = self.c.create_user_token("user", client="python", testing=True)
        payload = jwt.decode(token, self.c.api_secret, algorithms=["HS256"])
        self.assertEqual(payload["client"], "python")
        self.assertEqual(payload["testing"], True)

    def test_add_activity(self):
        feed = getfeed("user", "py1")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        response = feed.add_activity(activity_data)
        activity_id = response["id"]
        activities = feed.get(limit=1)["results"]
        self.assertEqual(activities[0]["id"], activity_id)

    def test_add_activity_to_inplace_change(self):
        feed = getfeed("user", "py1")
        team_feed = getfeed("user", "teamy")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        activity_data["to"] = [team_feed.id]
        feed.add_activity(activity_data)

        self.assertEqual(activity_data["to"], [team_feed.id])

    def test_add_activities_to_inplace_change(self):
        feed = getfeed("user", "py1")
        team_feed = getfeed("user", "teamy")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        activity_data["to"] = [team_feed.id]
        feed.add_activities([activity_data])

        self.assertEqual(activity_data["to"], [team_feed.id])

    def test_add_activity_to(self):
        # test for sending an activities to the team feed using to
        feeds = ["user", "teamy", "team_follower"]
        user_feed, team_feed, team_follower_feed = map(
            lambda x: getfeed("user", x), feeds
        )
        team_follower_feed.follow(team_feed.slug, team_feed.user_id)
        activity_data = {"actor": 1, "verb": "tweet", "object": 1, "to": [team_feed.id]}
        response = user_feed.add_activity(activity_data)
        activity_id = response["id"]

        # see if the new activity is also in the team feed
        activities = team_feed.get(limit=1)["results"]
        self.assertEqual(activities[0]["id"], activity_id)
        self.assertEqual(activities[0]["origin"], None)
        # see if the fanout process also works
        activities = team_follower_feed.get(limit=1)["results"]
        self.assertEqual(activities[0]["id"], activity_id)
        self.assertEqual(activities[0]["origin"], team_feed.id)
        # and validate removing also works
        user_feed.remove_activity(response["id"])
        # check the user pyto feed
        activities = team_feed.get(limit=1)["results"]
        self.assertFirstActivityIDNotEqual(activities, activity_id)
        # and the flat feed
        activities = team_follower_feed.get(limit=1)["results"]
        self.assertFirstActivityIDNotEqual(activities, activity_id)

    def test_add_activity_to_type_error(self):
        user_feed = getfeed("user", "1")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1, "to": "string"}

        self.assertRaises(TypeError, user_feed.add_activity, activity_data)

    def assertFirstActivityIDEqual(self, activities, correct_activity_id):
        activity_id = None
        if activities:
            activity_id = activities[0]["id"]
        self.assertEqual(activity_id, correct_activity_id)

    def assertFirstActivityIDNotEqual(self, activities, correct_activity_id):
        activity_id = None
        if activities:
            activity_id = activities[0]["id"]
        self.assertNotEqual(activity_id, correct_activity_id)

    def test_remove_activity(self):
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}

        activity_id = self.user1.add_activity(activity_data)["id"]
        activities = self.user1.get(limit=8)["results"]
        self.assertEqual(len(activities), 1)

        self.user1.remove_activity(activity_id)
        # verify that no activities were returned
        activities = self.user1.get(limit=8)["results"]
        self.assertEqual(len(activities), 0)

    def test_remove_activity_by_foreign_id(self):
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": "tweet:10",
        }

        self.user1.add_activity(activity_data)
        activities = self.user1.get(limit=8)["results"]
        self.assertEqual(len(activities), 1)
        self.assertNotEqual(activities[0]["id"], "")
        self.assertEqual(activities[0]["foreign_id"], "tweet:10")

        self.user1.remove_activity(foreign_id="tweet:10")
        # verify that no activities were returned
        activities = self.user1.get(limit=8)["results"]
        self.assertEqual(len(activities), 0)

        # verify this doesn't raise an error, but fails silently
        self.user1.remove_activity(foreign_id="tweet:unknownandmissing")

    def test_add_activities(self):
        activity_data = [
            {"actor": 1, "verb": "tweet", "object": 1},
            {"actor": 2, "verb": "watch", "object": 2},
        ]
        response = self.user1.add_activities(activity_data)
        activity_ids = [a["id"] for a in response["activities"]]
        activities = self.user1.get(limit=2)["results"]
        get_activity_ids = [a["id"] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])

    def test_add_activities_to(self):
        pyto2 = getfeed("user", "pyto2")
        pyto3 = getfeed("user", "pyto3")

        to = [pyto2.id, pyto3.id]
        activity_data = [
            {"actor": 1, "verb": "tweet", "object": 1, "to": to},
            {"actor": 2, "verb": "watch", "object": 2, "to": to},
        ]
        response = self.user1.add_activities(activity_data)
        activity_ids = [a["id"] for a in response["activities"]]
        activities = self.user1.get(limit=2)["results"]
        get_activity_ids = [a["id"] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])
        # test first target
        activities = pyto2.get(limit=2)["results"]
        get_activity_ids = [a["id"] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])
        # test second target
        activities = pyto3.get(limit=2)["results"]
        get_activity_ids = [a["id"] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])

    def test_follow_and_source(self):
        feed = getfeed("user", "test_follow")
        agg_feed = getfeed("aggregated", "test_follow")
        actor_id = random.randint(10, 100000)
        activity_data = {"actor": actor_id, "verb": "tweet", "object": 1}
        activity_id = feed.add_activity(activity_data)["id"]
        agg_feed.follow(feed.slug, feed.user_id)

        activities = agg_feed.get(limit=3)["results"]
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity["id"] if activity is not None else None
        self.assertEqual(activity["origin"], feed.id)
        self.assertEqual(activity_id_found, activity_id)

    def test_follow_activity_copy_limit(self):
        feed = getfeed("user", "test_follow_acl")
        feed1 = getfeed("user", "test_follow_acl1")
        actor_id = random.randint(10, 100000)
        feed1.add_activity({"actor": actor_id, "verb": "tweet", "object": 1})
        feed.follow(feed1.slug, feed1.user_id, activity_copy_limit=0)

        activities = feed.get(limit=5)["results"]

        self.assertEqual(len(activities), 0)

    def test_follow_and_delete(self):
        user_feed = getfeed("user", "test_follow")
        agg_feed = getfeed("aggregated", "test_follow")
        actor_id = random.randint(10, 100000)
        activity_data = {"actor": actor_id, "verb": "tweet", "object": 1}
        activity_id = user_feed.add_activity(activity_data)["id"]
        agg_feed.follow(user_feed.slug, user_feed.user_id)
        user_feed.remove_activity(activity_id)
        activities = agg_feed.get(limit=3)["results"]
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity["id"] if activity is not None else None

        self.assertNotEqual(activity_id_found, activity_id)

    def test_flat_follow(self):
        feed = getfeed("user", "test_flat_follow")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        activity_id = feed.add_activity(activity_data)["id"]
        self.flat3.follow(feed.slug, feed.user_id)

        activities = self.flat3.get(limit=3)["results"]
        activity = self._get_first_activity(activities)
        activity_id_found = activity["id"] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

        self.flat3.unfollow(feed.slug, feed.user_id)
        activities = self.flat3.get(limit=3)["results"]
        self.assertEqual(len(activities), 0)

    def test_flat_follow_no_copy(self):
        feed = getfeed("user", "test_flat_follow_no_copy")
        follower = getfeed("flat", "test_flat_follow_no_copy")
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        feed.add_activity(activity_data)
        follower.follow(feed.slug, feed.user_id, activity_copy_limit=0)

        activities = follower.get(limit=3)["results"]
        self.assertEqual(activities, [])

    def test_flat_follow_copy_one(self):
        feed = getfeed("user", "test_flat_follow_copy_one")
        follower = getfeed("flat", "test_flat_follow_copy_one")
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": "test:1",
        }
        feed.add_activity(activity_data)
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": "test:2",
        }
        feed.add_activity(activity_data)
        follower.follow(feed.slug, feed.user_id, activity_copy_limit=1)

        activities = follower.get(limit=3)["results"]
        # verify we get the latest activity
        self.assertEqual(activities[0]["foreign_id"], "test:2")

    def _get_first_aggregated_activity(self, activities):
        try:
            return activities[0]["activities"][0]
        except IndexError:
            pass

    def _get_first_activity(self, activities):
        try:
            return activities[0]
        except IndexError:
            pass

    def test_empty_followings(self):
        asocial = getfeed("user", "asocialpython")
        followings = asocial.following()
        self.assertEqual(followings["results"], [])

    def test_get_followings(self):
        social = getfeed("user", "psocial")
        social.follow("user", "apy")
        social.follow("user", "bpy")
        social.follow("user", "cpy")
        followings = social.following(offset=0, limit=2)
        self.assertEqual(len(followings["results"]), 2)
        self.assertEqual(followings["results"][0]["feed_id"], social.id)
        self.assertEqual(followings["results"][0]["target_id"], "user:cpy")
        followings = social.following(offset=1, limit=2)
        self.assertEqual(len(followings["results"]), 2)
        self.assertEqual(followings["results"][0]["feed_id"], social.id)
        self.assertEqual(followings["results"][0]["target_id"], "user:bpy")

    def test_empty_followers(self):
        asocial = getfeed("user", "asocialpython")
        followers = asocial.followers()
        self.assertEqual(len(followers["results"]), 0)
        self.assertEqual(followers["results"], [])

    def test_get_followers(self):
        social = getfeed("user", "psocial")
        spammy1 = getfeed("user", "spammy1")
        spammy2 = getfeed("user", "spammy2")
        spammy3 = getfeed("user", "spammy3")
        for feed in [spammy1, spammy2, spammy3]:
            feed.follow("user", social.user_id)
        followers = social.followers(offset=0, limit=2)
        self.assertEqual(len(followers["results"]), 2)
        self.assertEqual(followers["results"][0]["feed_id"], spammy3.id)
        self.assertEqual(followers["results"][0]["target_id"], social.id)
        followers = social.followers(offset=1, limit=2)
        self.assertEqual(len(followers["results"]), 2)
        self.assertEqual(followers["results"][0]["feed_id"], spammy2.id)
        self.assertEqual(followers["results"][0]["target_id"], social.id)

    def test_empty_do_i_follow(self):
        social = getfeed("user", "psocial")
        social.follow("user", "apy")
        social.follow("user", "bpy")
        followings = social.following(feeds=["user:missingpy"])
        self.assertEqual(len(followings["results"]), 0)
        self.assertEqual(followings["results"], [])

    def test_do_i_follow(self):
        social = getfeed("user", "psocial")
        social.follow("user", "apy")
        social.follow("user", "bpy")
        followings = social.following(feeds=["user:apy"])
        self.assertEqual(len(followings["results"]), 1)
        self.assertEqual(followings["results"][0]["feed_id"], social.id)
        self.assertEqual(followings["results"][0]["target_id"], "user:apy")

    def test_update_activity_to_targets(self):
        now = datetime.datetime.utcnow().isoformat()
        foreign_id = "user:1"
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": foreign_id,
            "time": now,
        }
        activity_data["to"] = ["user:1", "user:2"]
        self.user1.add_activity(activity_data)

        ret = self.user1.update_activity_to_targets(
            foreign_id, now, new_targets=["user:3", "user:2"]
        )
        self.assertEqual(len(ret["activity"]["to"]), 2)
        self.assertTrue("user:2" in ret["activity"]["to"])
        self.assertTrue("user:3" in ret["activity"]["to"])

        ret = self.user1.update_activity_to_targets(
            foreign_id,
            now,
            added_targets=["user:4", "user:5"],
            removed_targets=["user:3"],
        )
        self.assertEqual(len(ret["activity"]["to"]), 3)
        self.assertTrue("user:2" in ret["activity"]["to"])
        self.assertTrue("user:4" in ret["activity"]["to"])
        self.assertTrue("user:5" in ret["activity"]["to"])

    def test_get(self):
        activity_data = {"actor": 1, "verb": "tweet", "object": 1}
        activity_id = self.user1.add_activity(activity_data)["id"]
        activity_data = {"actor": 2, "verb": "add", "object": 2}
        activity_id_two = self.user1.add_activity(activity_data)["id"]
        activity_data = {"actor": 3, "verb": "watch", "object": 2}
        activity_id_three = self.user1.add_activity(activity_data)["id"]
        activities = self.user1.get(limit=2)["results"]
        # verify the first two results
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0]["id"], activity_id_three)
        self.assertEqual(activities[1]["id"], activity_id_two)
        # try offset based
        activities = self.user1.get(limit=2, offset=1)["results"]
        self.assertEqual(activities[0]["id"], activity_id_two)
        # try id_lt based
        activities = self.user1.get(limit=2, id_lt=activity_id_two)["results"]
        self.assertEqual(activities[0]["id"], activity_id)

    def test_get_not_marked_seen(self):
        notification_feed = getfeed("notification", "test_mark_seen")
        activities = notification_feed.get(limit=3)["results"]
        for activity in activities:
            self.assertFalse(activity["is_seen"])

    def test_mark_seen_on_get(self):
        notification_feed = getfeed("notification", "test_mark_seen")
        activities = notification_feed.get(limit=100)["results"]
        for activity in activities:
            notification_feed.remove_activity(activity["id"])

        old_activities = [
            notification_feed.add_activity({"actor": 1, "verb": "tweet", "object": 1}),
            notification_feed.add_activity({"actor": 2, "verb": "add", "object": 2}),
            notification_feed.add_activity({"actor": 3, "verb": "watch", "object": 3}),
        ]

        notification_feed.get(
            mark_seen=[old_activities[0]["id"], old_activities[1]["id"]]
        )

        activities = notification_feed.get(limit=3)["results"]

        # is the seen state correct
        for activity in activities:
            # using a loop in case we're retrieving activities in a different order than old_activities
            if old_activities[0]["id"] == activity["id"]:
                self.assertTrue(activity["is_seen"])
            if old_activities[1]["id"] == activity["id"]:
                self.assertTrue(activity["is_seen"])
            if old_activities[2]["id"] == activity["id"]:
                self.assertFalse(activity["is_seen"])

        # see if the state properly resets after we add another activity
        notification_feed.add_activity(
            {"actor": 3, "verb": "watch", "object": 3}
        )  # ['id']
        activities = notification_feed.get(limit=3)["results"]
        self.assertFalse(activities[0]["is_seen"])
        self.assertEqual(len(activities[0]["activities"]), 2)

    def test_mark_read_by_id(self):
        notification_feed = getfeed("notification", "py2")

        activities = notification_feed.get(limit=3)["results"]
        ids = []
        for activity in activities:
            ids.append(activity["id"])
            self.assertFalse(activity["is_read"])
        ids = ids[:2]
        notification_feed.get(mark_read=ids)
        activities = notification_feed.get(limit=3)["results"]
        for activity in activities:
            if activity["id"] in ids:
                self.assertTrue(activity["is_read"])
                self.assertFalse(activity["is_seen"])

    def test_api_key_exception(self):
        self.c = stream.connect(
            "5crf3bhfzesnMISSING",
            "tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su",
        )
        self.user1 = self.c.feed("user", "1")
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "debug_example_undefined": "test",
        }
        self.assertRaises(
            ApiKeyException, lambda: self.user1.add_activity(activity_data)
        )

    def test_complex_field(self):
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "participants": ["Tommaso", "Thierry"],
        }
        response = self.user1.add_activity(activity_data)
        activity_id = response["id"]
        activities = self.user1.get(limit=1)["results"]
        self.assertEqual(activities[0]["id"], activity_id)
        self.assertEqual(activities[0]["participants"], ["Tommaso", "Thierry"])

    def assertDatetimeAlmostEqual(self, a, b):
        difference = abs(a - b)
        if difference > datetime.timedelta(milliseconds=1):
            self.assertEqual(a, b)

    def assertClearlyNotEqual(self, a, b):
        difference = abs(a - b)
        if difference < datetime.timedelta(milliseconds=1):
            raise ValueError("the dates are too close")

    def test_uniqueness(self):
        """
        In order for things to be considere unique they need:
        a.) The same time and activity data
        b.) The same time and foreign id
        """

        utcnow = datetime.datetime.now(tz=pytz.utc)
        activity_data = {"actor": 1, "verb": "tweet", "object": 1, "time": utcnow}
        self.user1.add_activity(activity_data)
        self.user1.add_activity(activity_data)

        activities = self.user1.get(limit=2)["results"]
        self.assertDatetimeAlmostEqual(activities[0]["time"], utcnow)
        if len(activities) > 1:
            self.assertClearlyNotEqual(activities[1]["time"], utcnow)

    def test_uniqueness_topic(self):
        """
        In order for things to be considere unique they need:
        a.) The same time and activity data, or
        b.) The same time and foreign id
        """
        # follow both the topic and the user
        self.flat3.follow("topic", self.topic1.user_id)
        self.flat3.follow("user", self.user1.user_id)
        # add the same activity twice
        now = datetime.datetime.now(tzlocal())
        tweet = "My Way %s" % get_unique_postfix()
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "time": now,
            "tweet": tweet,
        }
        self.topic1.add_activity(activity_data)
        self.user1.add_activity(activity_data)
        # verify that flat3 contains the activity exactly once
        response = self.flat3.get(limit=3)
        activity_tweets = [a.get("tweet") for a in response["results"]]
        self.assertEqual(activity_tweets.count(tweet), 1)

    def test_uniqueness_foreign_id(self):
        now = datetime.datetime.now(tzlocal())
        utcnow = now.astimezone(pytz.utc)

        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": "tweet:11",
            "time": utcnow,
        }
        self.user1.add_activity(activity_data)

        activity_data = {
            "actor": 2,
            "verb": "tweet",
            "object": 3,
            "foreign_id": "tweet:11",
            "time": utcnow,
        }
        self.user1.add_activity(activity_data)

        activities = self.user1.get(limit=10)["results"]
        # the second post should have overwritten the first one (because they
        # had same id)

        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0]["object"], "3")
        self.assertEqual(activities[0]["foreign_id"], "tweet:11")
        self.assertDatetimeAlmostEqual(activities[0]["time"], utcnow)

    def test_time_ordering(self):
        """
        datetime.datetime.now(tz=pytz.utc) is our recommended approach
        so if we add an activity
        add one using time
        add another activity it should be in the right spot
        """

        # timedelta is used to "make sure" that ordering is known even though
        # server time is not
        custom_time = datetime.datetime.now(tz=pytz.utc) - datetime.timedelta(days=1)

        feed = self.user2
        for index, activity_time in enumerate([None, custom_time, None]):
            self._test_sleep(1, 1)  # so times are a bit different
            activity_data = {
                "actor": 1,
                "verb": "tweet",
                "object": 1,
                "foreign_id": "tweet:%s" % index,
                "time": activity_time,
            }
            feed.add_activity(activity_data)

        activities = feed.get(limit=3)["results"]
        # the second post should have overwritten the first one (because they
        # had same id)
        self.assertEqual(activities[0]["foreign_id"], "tweet:2")
        self.assertEqual(activities[1]["foreign_id"], "tweet:0")
        self.assertEqual(activities[2]["foreign_id"], "tweet:1")
        self.assertDatetimeAlmostEqual(activities[2]["time"], custom_time)

    def test_missing_actor(self):
        activity_data = {
            "verb": "tweet",
            "object": 1,
            "debug_example_undefined": "test",
        }
        try:
            self.user1.add_activity(activity_data)
            raise ValueError("should have raised InputException")
        except InputException:
            pass

    def test_wrong_feed_spec(self):
        self.assertRaises(TypeError, lambda: getfeed("user1"))

    def test_serialization(self):
        today = datetime.date.today()
        now = datetime.datetime.now(tz=pytz.utc)
        then = now.replace(microsecond=0)
        data = dict(
            string="string",
            float=0.1,
            int=1,
            date=today,
            datetime=now,
            datetimenomicro=then,
        )
        serialized = serializer.dumps(data)
        loaded = serializer.loads(serialized)
        self.assertEqual(data, loaded)

    def test_follow_many(self):
        sources = [getfeed("user", str(i)).id for i in range(10)]
        targets = [getfeed("flat", str(i)).id for i in range(10)]
        feeds = [{"source": s, "target": t} for s, t in zip(sources, targets)]
        self.c.follow_many(feeds)

        for target in targets:
            follows = self.c.feed(*target.split(":")).followers()["results"]
            self.assertEqual(len(follows), 1)
            self.assertTrue(follows[0]["feed_id"] in sources)
            self.assertEqual(follows[0]["target_id"], target)

        for source in sources:
            follows = self.c.feed(*source.split(":")).following()["results"]
            self.assertEqual(len(follows), 1)
            self.assertEqual(follows[0]["feed_id"], source)
            self.assertTrue(follows[0]["target_id"] in targets)

    def test_follow_many_acl(self):
        sources = [getfeed("user", str(i)) for i in range(10)]
        # ensure every source is empty first
        for feed in sources:
            activities = feed.get(limit=100)["results"]
            for activity in activities:
                feed.remove_activity(activity["id"])

        targets = [getfeed("flat", str(i)) for i in range(10)]
        # ensure every source is empty first
        for feed in targets:
            activities = feed.get(limit=100)["results"]
            for activity in activities:
                feed.remove_activity(activity["id"])
        # add activity to each target feed
        activity = {
            "actor": "barry",
            "object": "09",
            "verb": "tweet",
            "time": datetime.datetime.utcnow().isoformat(),
        }
        for feed in targets:
            feed.add_activity(activity)
            self.assertEqual(len(feed.get(limit=5)["results"]), 1)

        sources_id = [feed.id for feed in sources]
        targets_id = [target.id for target in targets]
        feeds = [{"source": s, "target": t} for s, t in zip(sources_id, targets_id)]

        self.c.follow_many(feeds, activity_copy_limit=0)

        for feed in sources:
            activities = feed.get(limit=5)["results"]
            self.assertEqual(len(activities), 0)

    def test_unfollow_many(self):
        unfollows = [
            {"source": "user:1", "target": "timeline:1"},
            {"source": "user:2", "target": "timeline:2", "keep_history": False},
        ]

        self.c.unfollow_many(unfollows)

        unfollows.append({"source": "user:1", "target": 42})

        def failing_unfollow():
            self.c.unfollow_many(unfollows)

        self.assertRaises(InputException, failing_unfollow)

    def test_add_to_many(self):
        activity = {"actor": 1, "verb": "tweet", "object": 1, "custom": "data"}
        feeds = [getfeed("flat", str(i)).id for i in range(10, 20)]
        self.c.add_to_many(activity, feeds)

        for feed in feeds:
            feed = self.c.feed(*feed.split(":"))
            self.assertEqual(feed.get()["results"][0]["custom"], "data")

    def test_create_email_redirect(self):
        target_url = "http://google.com/?a=b&c=d"
        user_id = "tommaso"

        impression = {
            "foreign_ids": ["tweet:1", "tweet:2", "tweet:3", "tweet:4", "tweet:5"],
            "feed_id": "user:global",
            "user_id": user_id,
            "location": "email",
        }
        engagement = {
            "user_id": user_id,
            "label": "click",
            "feed_id": "user:global",
            "location": "email",
            "position": 3,
            "foreign_id": "tweet:1",
        }
        events = [impression, engagement]

        redirect_url = self.c.create_redirect_url(target_url, user_id, events)

        parsed_url = urlparse(redirect_url)
        qs = parse_qs(parsed_url.query)

        decoded = jwt.decode(
            qs["authorization"][0], self.c.api_secret, algorithms=["HS256"]
        )

        self.assertEqual(
            decoded,
            {
                "resource": "redirect_and_track",
                "action": "*",
                "feed_id": "*",
                "user_id": "tommaso",
            },
        )

        expected_params = {
            "auth_type": "jwt",
            "url": target_url,
            "api_key": self.c.api_key,
        }

        for k, v in expected_params.items():
            self.assertEqual(qs[k][0], v)

        self.assertEqual(json.loads(qs["events"][0]), events)

    def test_email_redirect_invalid_target(self):
        engagement = {
            "foreign_id": "tweet:1",
            "label": "click",
            "position": 3,
            "user_id": "tommaso",
            "location": "email",
            "feed_id": "user:global",
        }
        impression = {
            "foreign_ids": ["tweet:1", "tweet:2", "tweet:3", "tweet:4", "tweet:5"],
            "user_id": "tommaso",
            "location": "email",
            "feed_id": "user:global",
        }
        events = [impression, engagement]
        # no protocol specified, this should raise an error
        target_url = "google.com"
        user_id = "tommaso"

        def redirect():
            self.c.create_redirect_url(target_url, user_id, events)

        self.assertRaises(MissingSchema, redirect)

    def test_follow_redirect_url(self):
        target_url = "http://google.com/?a=b&c=d"
        events = []
        user_id = "tommaso"
        redirect_url = self.c.create_redirect_url(target_url, user_id, events)

        res = requests.get(redirect_url)
        res.raise_for_status()
        self.assertTrue("google" in res.url)

    def test_get_activities_empty_ids(self):
        response = self.c.get_activities(ids=[str(uuid1())])
        self.assertEqual(len(response["results"]), 0)

    def test_get_activities_empty_foreign_ids(self):
        response = self.c.get_activities(
            foreign_id_times=[("fid-x", datetime.datetime.utcnow())]
        )
        self.assertEqual(len(response["results"]), 0)

    def test_get_activities_full(self):
        dt = datetime.datetime.utcnow()
        fid = "awesome-test"

        activity = {
            "actor": "barry",
            "object": "09",
            "verb": "tweet",
            "time": dt,
            "foreign_id": fid,
        }

        feed = getfeed("user", "test_get_activity")
        response = feed.add_activity(activity)

        response = self.c.get_activities(ids=[response["id"]])
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(activity["foreign_id"], response["results"][0]["foreign_id"])

        response = self.c.get_activities(foreign_id_times=[(fid, dt)])
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(activity["foreign_id"], response["results"][0]["foreign_id"])

    def test_get_activities_full_with_enrichment(self):
        dt = datetime.datetime.utcnow()
        fid = "awesome-test"

        actor = self.c.users.add(str(uuid1()), data={"name": "barry"})
        activity = {
            "actor": self.c.users.create_reference(actor["id"]),
            "object": "09",
            "verb": "tweet",
            "time": dt,
            "foreign_id": fid,
        }

        feed = getfeed("user", "test_get_activity")
        activity = feed.add_activity(activity)

        reaction1 = self.c.reactions.add("like", activity["id"], "liker")
        reaction2 = self.c.reactions.add("reshare", activity["id"], "sharer")

        def validate(response):
            self.assertEqual(len(response["results"]), 1)
            self.assertEqual(response["results"][0]["id"], activity["id"])
            self.assertEqual(
                response["results"][0]["foreign_id"], activity["foreign_id"]
            )
            self.assertEqual(response["results"][0]["actor"]["data"]["name"], "barry")
            latest_reactions = response["results"][0]["latest_reactions"]
            self.assertEqual(len(latest_reactions), 2)
            self.assertEqual(latest_reactions["like"][0]["id"], reaction1["id"])
            self.assertEqual(latest_reactions["reshare"][0]["id"], reaction2["id"])
            self.assertEqual(
                response["results"][0]["reaction_counts"], {"like": 1, "reshare": 1}
            )

        reactions = {"recent": True, "counts": True}
        validate(self.c.get_activities(ids=[activity["id"]], reactions=reactions))
        validate(
            self.c.get_activities(foreign_id_times=[(fid, dt)], reactions=reactions)
        )

    def test_get_activities_full_with_enrichment_and_reaction_kinds(self):
        dt = datetime.datetime.utcnow()
        fid = "awesome-test"

        actor = self.c.users.add(str(uuid1()), data={"name": "barry"})
        activity = {
            "actor": self.c.users.create_reference(actor["id"]),
            "object": "09",
            "verb": "tweet",
            "time": dt,
            "foreign_id": fid,
        }

        feed = getfeed("user", "test_get_activity")
        activity = feed.add_activity(activity)

        self.c.reactions.add("like", activity["id"], "liker")
        self.c.reactions.add("reshare", activity["id"], "sharer")
        self.c.reactions.add("comment", activity["id"], "commenter")

        reactions = {"recent": True, "counts": True, "kinds": "like,comment"}
        response = self.c.get_activities(ids=[activity["id"]], reactions=reactions)
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["id"], activity["id"])
        self.assertEqual(
            sorted(response["results"][0]["latest_reactions"].keys()),
            ["comment", "like"],
        )
        self.assertEqual(
            response["results"][0]["reaction_counts"], {"like": 1, "comment": 1}
        )

        reactions = {
            "recent": True,
            "counts": True,
            "kinds": ["", "reshare   ", "comment\n"],
        }
        response = self.c.get_activities(
            foreign_id_times=[(fid, dt)], reactions=reactions
        )
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0]["id"], activity["id"])
        self.assertEqual(
            sorted(response["results"][0]["latest_reactions"].keys()),
            ["comment", "reshare"],
        )
        self.assertEqual(
            response["results"][0]["reaction_counts"], {"comment": 1, "reshare": 1}
        )

    def test_activity_partial_update(self):
        now = datetime.datetime.utcnow()
        feed = self.c.feed("user", uuid4())
        feed.add_activity(
            {
                "actor": "barry",
                "object": "09",
                "verb": "tweet",
                "time": now,
                "foreign_id": "fid:123",
                "product": {"name": "shoes", "price": 9.99, "color": "blue"},
            }
        )
        activity = feed.get()["results"][0]

        to_set = {
            "product.name": "boots",
            "product.price": 7.99,
            "popularity": 1000,
            "foo": {"bar": {"baz": "qux"}},
        }
        to_unset = ["product.color"]

        # partial update by ID
        self.c.activity_partial_update(id=activity["id"], set=to_set, unset=to_unset)
        updated = feed.get()["results"][0]
        expected = activity
        expected["product"] = {"name": "boots", "price": 7.99}
        expected["popularity"] = 1000
        expected["foo"] = {"bar": {"baz": "qux"}}
        self.assertEqual(updated, expected)

        # partial update by foreign ID + time
        to_set = {"foo.bar.baz": 42, "popularity": 9000}
        to_unset = ["product.price"]
        self.c.activity_partial_update(
            foreign_id=activity["foreign_id"],
            time=activity["time"],
            set=to_set,
            unset=to_unset,
        )
        updated = feed.get()["results"][0]
        expected["product"] = {"name": "boots"}
        expected["foo"] = {"bar": {"baz": 42}}
        expected["popularity"] = 9000
        self.assertEqual(updated, expected)

    def test_activities_partial_update(self):

        feed = self.c.feed("user", uuid4())
        feed.add_activities(
            [
                {
                    "actor": "barry",
                    "object": "09",
                    "verb": "tweet",
                    "time": datetime.datetime.utcnow(),
                    "foreign_id": "fid:123",
                    "product": {"name": "shoes", "price": 9.99, "color": "blue"},
                },
                {
                    "actor": "jerry",
                    "object": "10",
                    "verb": "tweet",
                    "time": datetime.datetime.utcnow(),
                    "foreign_id": "fid:456",
                    "product": {"name": "shoes", "price": 9.99, "color": "blue"},
                },
                {
                    "actor": "tommy",
                    "object": "09",
                    "verb": "tweet",
                    "time": datetime.datetime.utcnow(),
                    "foreign_id": "fid:789",
                    "product": {"name": "shoes", "price": 9.99, "color": "blue"},
                },
            ]
        )
        activities = feed.get()["results"]

        batch = [
            {
                "id": activities[0]["id"],
                "set": {"product.color": "purple", "custom": {"some": "extra data"}},
                "unset": ["product.price"],
            },
            {
                "id": activities[2]["id"],
                "set": {"product.price": 9001, "on_sale": True},
            },
        ]

        # partial update by ID
        self.c.activities_partial_update(batch)
        updated = feed.get()["results"]
        expected = activities
        expected[0]["product"] = {"name": "shoes", "color": "purple"}
        expected[0]["custom"] = {"some": "extra data"}
        expected[2]["product"] = {"name": "shoes", "price": 9001, "color": "blue"}
        expected[2]["on_sale"] = True
        self.assertEqual(updated, expected)

        # partial update by foreign ID + time
        batch = [
            {
                "foreign_id": activities[1]["foreign_id"],
                "time": activities[1]["time"],
                "set": {"product.color": "beeeeeeige", "custom": {"modified_by": "me"}},
                "unset": ["product.name"],
            },
            {
                "foreign_id": activities[2]["foreign_id"],
                "time": activities[2]["time"],
                "unset": ["on_sale"],
            },
        ]
        self.c.activities_partial_update(batch)
        updated = feed.get()["results"]

        expected[1]["product"] = {"price": 9.99, "color": "beeeeeeige"}
        expected[1]["custom"] = {"modified_by": "me"}
        del expected[2]["on_sale"]
        self.assertEqual(updated, expected)

    def test_create_reference(self):
        ref = self.c.collections.create_reference("item", "42")
        self.assertEqual(ref, "SO:item:42")

    def test_create_user_reference(self):
        ref = self.c.users.create_reference("42")
        self.assertEqual(ref, "SU:42")

    def test_reaction_add(self):
        self.c.reactions.add("like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike")

    def test_reaction_add_to_target_feeds(self):
        r = self.c.reactions.add(
            "superlike",
            "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4",
            "mike",
            data={"popularity": 50},
            target_feeds=["user:michelle"],
            target_feeds_extra_data={"popularity": 100},
        )
        self.assertEqual(r["data"]["popularity"], 50)
        a = self.c.feed("user", "michelle").get(limit=1)["results"][0]
        self.assertTrue(r["id"] in a["reaction"])
        self.assertEqual(a["verb"], "superlike")
        self.assertEqual(a["popularity"], 100)

        child = self.c.reactions.add_child(
            "superlike",
            r["id"],
            "rob",
            data={"popularity": 60},
            target_feeds=["user:michelle"],
            target_feeds_extra_data={"popularity": 200},
        )

        self.assertEqual(child["data"]["popularity"], 60)
        a = self.c.feed("user", "michelle").get(limit=1)["results"][0]
        self.assertTrue(child["id"] in a["reaction"])
        self.assertEqual(a["verb"], "superlike")
        self.assertEqual(a["popularity"], 200)

    def test_reaction_get(self):
        response = self.c.reactions.add(
            "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
        )
        reaction = self.c.reactions.get(response["id"])
        self.assertEqual(reaction["parent"], "")
        self.assertEqual(reaction["data"], {})
        self.assertEqual(reaction["latest_children"], {})
        self.assertEqual(reaction["children_counts"], {})
        self.assertEqual(
            reaction["activity_id"], "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4"
        )
        self.assertEqual(reaction["kind"], "like")
        self.assertTrue("created_at" in reaction)
        self.assertTrue("updated_at" in reaction)
        self.assertTrue("id" in reaction)

    def test_reaction_update(self):
        response = self.c.reactions.add(
            "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
        )
        self.c.reactions.update(response["id"], {"changed": True})

    def test_reaction_delete(self):
        response = self.c.reactions.add(
            "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
        )
        self.c.reactions.delete(response["id"])

    def test_reaction_add_child(self):
        response = self.c.reactions.add(
            "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
        )
        self.c.reactions.add_child("like", response["id"], "rob")

    def test_reaction_filter_random(self):
        self.c.reactions.filter(
            kind="like",
            reaction_id="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
            id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
        )
        self.c.reactions.filter(
            activity_id="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
            id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
        )
        self.c.reactions.filter(
            user_id="mike", id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b"
        )

    def _first_result_should_be(self, response, element):
        el = element.copy()
        el.pop("duration")
        self.assertEqual(len(response["results"]), 1)
        self.assertEqual(response["results"][0], el)

    def test_reaction_filter(self):
        activity_id = str(uuid1())
        user = str(uuid1())

        response = self.c.reactions.add("like", activity_id, user)
        child = self.c.reactions.add_child("like", response["id"], user)
        reaction = self.c.reactions.get(response["id"])

        response = self.c.reactions.add("comment", activity_id, user)
        reaction_comment = self.c.reactions.get(response["id"])

        r = self.c.reactions.filter(reaction_id=reaction["id"])
        self._first_result_should_be(r, child)

        r = self.c.reactions.filter(
            kind="like", activity_id=activity_id, id_lte=reaction["id"]
        )
        self._first_result_should_be(r, reaction)

        r = self.c.reactions.filter(kind="like", user_id=user, id_lte=reaction["id"])
        self._first_result_should_be(r, reaction)

        r = self.c.reactions.filter(kind="comment", activity_id=activity_id)
        self._first_result_should_be(r, reaction_comment)

    def test_user_add(self):
        self.c.users.add(str(uuid1()))

    def test_user_add_get_or_create(self):
        user_id = str(uuid1())
        r1 = self.c.users.add(user_id)
        r2 = self.c.users.add(user_id, get_or_create=True)
        self.assertEqual(r1["id"], r2["id"])
        self.assertEqual(r1["created_at"], r2["created_at"])
        self.assertEqual(r1["updated_at"], r2["updated_at"])

    def test_user_get(self):
        response = self.c.users.add(str(uuid1()))
        user = self.c.users.get(response["id"])
        self.assertEqual(user["data"], {})
        self.assertTrue("created_at" in user)
        self.assertTrue("updated_at" in user)
        self.assertTrue("id" in user)

    def test_user_get_with_follow_counts(self):
        response = self.c.users.add(str(uuid1()))
        user = self.c.users.get(response["id"], with_follow_counts=True)
        self.assertEqual(user["id"], response["id"])
        self.assertTrue("followers_count" in user)
        self.assertTrue("following_count" in user)

    def test_user_update(self):
        response = self.c.users.add(str(uuid1()))
        self.c.users.update(response["id"], {"changed": True})

    def test_user_delete(self):
        response = self.c.users.add(str(uuid1()))
        self.c.users.delete(response["id"])

    def test_collections_add(self):
        self.c.collections.add("items", {"data": 1}, id=str(uuid1()), user_id="tom")

    def test_collections_add_no_id(self):
        self.c.collections.add("items", {"data": 1})

    def test_collections_get(self):
        response = self.c.collections.add("items", {"data": 1}, id=str(uuid1()))
        entry = self.c.collections.get("items", response["id"])
        self.assertEqual(entry["data"], {"data": 1})
        self.assertTrue("created_at" in entry)
        self.assertTrue("updated_at" in entry)
        self.assertTrue("id" in entry)

    def test_collections_update(self):
        response = self.c.collections.add("items", {"data": 1}, str(uuid1()))
        self.c.collections.update("items", response["id"], data={"changed": True})
        entry = self.c.collections.get("items", response["id"])
        self.assertEqual(entry["data"], {"changed": True})

    def test_collections_delete(self):
        response = self.c.collections.add("items", {"data": 1}, str(uuid1()))
        self.c.collections.delete("items", response["id"])

    def test_feed_enrichment_collection(self):
        entry = self.c.collections.add("items", {"name": "time machine"})
        entry.pop("duration")
        f = getfeed("user", "mike")
        activity_data = {
            "actor": "mike",
            "verb": "buy",
            "object": self.c.collections.create_reference(entry=entry),
        }
        f.add_activity(activity_data)
        response = f.get()
        self.assertTrue(
            set(activity_data.items()).issubset(set(response["results"][0].items()))
        )
        enriched_response = f.get(enrich=True)
        self.assertEqual(enriched_response["results"][0]["object"], entry)

    def test_feed_enrichment_user(self):
        user = self.c.users.add(str(uuid1()), {"name": "Mike"})
        user.pop("duration")
        f = getfeed("user", "mike")
        activity_data = {
            "actor": self.c.users.create_reference(user),
            "verb": "buy",
            "object": "time machine",
        }
        f.add_activity(activity_data)
        response = f.get()
        self.assertTrue(
            set(activity_data.items()).issubset(set(response["results"][0].items()))
        )
        enriched_response = f.get(enrich=True)
        self.assertEqual(enriched_response["results"][0]["actor"], user)

    def test_feed_enrichment_own_reaction(self):
        f = getfeed("user", "mike")
        activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
        response = f.add_activity(activity_data)
        reaction = self.c.reactions.add("like", response["id"], "mike")
        reaction.pop("duration")
        enriched_response = f.get(reactions={"own": True}, user_id="mike")
        self.assertEqual(
            enriched_response["results"][0]["own_reactions"]["like"][0], reaction
        )

    def test_feed_enrichment_recent_reaction(self):
        f = getfeed("user", "mike")
        activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
        response = f.add_activity(activity_data)
        reaction = self.c.reactions.add("like", response["id"], "mike")
        reaction.pop("duration")
        enriched_response = f.get(reactions={"recent": True})
        self.assertEqual(
            enriched_response["results"][0]["latest_reactions"]["like"][0], reaction
        )

    def test_feed_enrichment_reaction_counts(self):
        f = getfeed("user", "mike")
        activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
        response = f.add_activity(activity_data)
        reaction = self.c.reactions.add("like", response["id"], "mike")
        reaction.pop("duration")
        enriched_response = f.get(reactions={"counts": True})
        self.assertEqual(enriched_response["results"][0]["reaction_counts"]["like"], 1)

    def test_track_engagements(self):
        engagements = [
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
        client.track_engagements(engagements)

    def test_track_impressions(self):
        impressions = [
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
        client.track_impressions(impressions)

    def test_og(self):
        response = client.og("https://google.com")
        self.assertTrue("title" in response)
        self.assertTrue("description" in response)

    def test_follow_stats(self):
        uniq = uuid4()
        f = client.feed("user", uniq)
        f.follow("user", uuid4())
        f.follow("user", uuid4())
        f.follow("user", uuid4())

        client.feed("user", uuid4()).follow("user", uniq)
        client.feed("timeline", uuid4()).follow("user", uniq)

        feed_id = "user:" + str(uniq)
        response = client.follow_stats(feed_id)["results"]
        self.assertEqual(response["following"]["count"], 3)
        self.assertEqual(response["followers"]["count"], 2)

        response = client.follow_stats(
            feed_id, followers_slugs=["timeline"], following_slugs=["timeline"]
        )["results"]
        self.assertEqual(response["following"]["count"], 0)
        self.assertEqual(response["followers"]["count"], 1)

    def test_token_type(self):
        """
        test to check whether token is a byte or string
        """
        with_bytes = Feed(client, "user", "1", b"token")
        self.assertEqual(with_bytes.token, "token")

        with_str = Feed(client, "user", "1", "token")
        self.assertEqual(with_str.token, "token")

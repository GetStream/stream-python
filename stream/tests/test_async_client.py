import asyncio
import random
from datetime import datetime, timedelta
from uuid import uuid1, uuid4

import pytz
import pytest
from dateutil.tz import tzlocal

import stream
from stream.exceptions import ApiKeyException, InputException
from stream.tests.test_client import get_unique_postfix


def assert_first_activity_id_equal(activities, correct_activity_id):
    activity_id = None
    if activities:
        activity_id = activities[0]["id"]
    assert activity_id == correct_activity_id


def assert_first_activity_id_not_equal(activities, correct_activity_id):
    activity_id = None
    if activities:
        activity_id = activities[0]["id"]
    assert activity_id != correct_activity_id


def _get_first_aggregated_activity(activities):
    try:
        return activities[0]["activities"][0]
    except IndexError:
        pass


def _get_first_activity(activities):
    try:
        return activities[0]
    except IndexError:
        pass


def assert_datetime_almost_equal(a, b):
    difference = abs(a - b)
    if difference > timedelta(milliseconds=1):
        assert a == b


def assert_clearly_not_equal(a, b):
    difference = abs(a - b)
    if difference < timedelta(milliseconds=1):
        raise ValueError("the dates are too close")


async def _test_sleep(production_wait):
    """
    when testing against a live API, sometimes we need a small sleep to
    ensure data stability, however when testing locally the wait does
    not need to be as long
    :param production_wait: float, number of seconds to sleep when hitting real API
    :return: None
    """
    sleep_time = production_wait
    await asyncio.sleep(sleep_time)


@pytest.mark.asyncio
async def test_update_activities_create(async_client):
    activities = [
        {
            "actor": "user:1",
            "verb": "do",
            "object": "object:1",
            "foreign_id": "object:1",
            "time": datetime.utcnow().isoformat(),
        }
    ]

    response = await async_client.update_activities(activities)
    assert response


@pytest.mark.asyncio
async def test_add_activity(async_client):
    feed = async_client.feed("user", "py1")
    activity_data = {"actor": 1, "verb": "tweet", "object": 1}
    response = await feed.add_activity(activity_data)
    activity_id = response["id"]
    response = await feed.get(limit=1)
    activities = response["results"]
    assert activities[0]["id"] == activity_id


@pytest.mark.asyncio
async def test_add_activity_to_inplace_change(async_client):
    feed = async_client.feed("user", "py1")
    team_feed = async_client.feed("user", "teamy")
    activity_data = {"actor": 1, "verb": "tweet", "object": 1}
    activity_data["to"] = [team_feed.id]
    await feed.add_activity(activity_data)
    assert activity_data["to"] == [team_feed.id]


@pytest.mark.asyncio
async def test_add_activities_to_inplace_change(async_client):
    feed = async_client.feed("user", "py1")
    team_feed = async_client.feed("user", "teamy")
    activity_data = {"actor": 1, "verb": "tweet", "object": 1}
    activity_data["to"] = [team_feed.id]
    await feed.add_activities([activity_data])
    assert activity_data["to"] == [team_feed.id]


@pytest.mark.asyncio
async def test_add_activity_to(async_client):
    # test for sending an activities to the team feed using to
    feeds = ["user", "teamy", "team_follower"]
    user_feed, team_feed, team_follower_feed = map(
        lambda x: async_client.feed("user", x), feeds
    )
    await team_follower_feed.follow(team_feed.slug, team_feed.user_id)
    activity_data = {"actor": 1, "verb": "tweet", "object": 1, "to": [team_feed.id]}
    activity = await user_feed.add_activity(activity_data)
    activity_id = activity["id"]

    # see if the new activity is also in the team feed
    response = await team_feed.get(limit=1)
    activities = response["results"]
    assert activities[0]["id"] == activity_id
    assert activities[0]["origin"] is None
    # see if the fanout process also works
    response = await team_follower_feed.get(limit=1)
    activities = response["results"]
    assert activities[0]["id"] == activity_id
    assert activities[0]["origin"] == team_feed.id
    # and validate removing also works
    await user_feed.remove_activity(activity["id"])
    # check the user pyto feed
    response = await team_feed.get(limit=1)
    activities = response["results"]
    assert_first_activity_id_not_equal(activities, activity_id)
    # and the flat feed
    response = await team_follower_feed.get(limit=1)
    activities = response["results"]
    assert_first_activity_id_not_equal(activities, activity_id)


@pytest.mark.asyncio
async def test_remove_activity(user1):
    activity_data = {"actor": 1, "verb": "tweet", "object": 1}
    activity = await user1.add_activity(activity_data)
    activity_id = activity["id"]
    response = await user1.get(limit=8)
    activities = response["results"]
    assert len(activities) == 1

    await user1.remove_activity(activity_id)
    # verify that no activities were returned
    response = await user1.get(limit=8)
    activities = response["results"]
    assert len(activities) == 0


@pytest.mark.asyncio
async def test_remove_activity_by_foreign_id(user1):
    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "foreign_id": "tweet:10",
    }

    await user1.add_activity(activity_data)
    response = await user1.get(limit=8)
    activities = response["results"]
    assert len(activities) == 1
    assert activities[0]["id"] != ""
    assert activities[0]["foreign_id"] == "tweet:10"

    await user1.remove_activity(foreign_id="tweet:10")
    # verify that no activities were returned
    response = await user1.get(limit=8)
    activities = response["results"]
    assert len(activities) == 0
    # verify this doesn't raise an error, but fails silently
    await user1.remove_activity(foreign_id="tweet:unknownandmissing")


@pytest.mark.asyncio
async def test_add_activities(user1):
    activity_data = [
        {"actor": 1, "verb": "tweet", "object": 1},
        {"actor": 2, "verb": "watch", "object": 2},
    ]
    response = await user1.add_activities(activity_data)
    activity_ids = [a["id"] for a in response["activities"]]
    response = await user1.get(limit=2)
    activities = response["results"]
    get_activity_ids = [a["id"] for a in activities]
    assert get_activity_ids == activity_ids[::-1]


@pytest.mark.asyncio
async def test_add_activities_to(async_client, user1):
    pyto2 = async_client.feed("user", "pyto2")
    pyto3 = async_client.feed("user", "pyto3")

    to = [pyto2.id, pyto3.id]
    activity_data = [
        {"actor": 1, "verb": "tweet", "object": 1, "to": to},
        {"actor": 2, "verb": "watch", "object": 2, "to": to},
    ]
    response = await user1.add_activities(activity_data)
    activity_ids = [a["id"] for a in response["activities"]]
    response = await user1.get(limit=2)
    activities = response["results"]
    get_activity_ids = [a["id"] for a in activities]
    assert get_activity_ids == activity_ids[::-1]
    # test first target
    response = await pyto2.get(limit=2)
    activities = response["results"]
    get_activity_ids = [a["id"] for a in activities]
    assert get_activity_ids == activity_ids[::-1]
    # test second target
    response = await pyto3.get(limit=2)
    activities = response["results"]
    get_activity_ids = [a["id"] for a in activities]
    assert get_activity_ids == activity_ids[::-1]


@pytest.mark.asyncio
async def test_follow_and_source(async_client):
    feed = async_client.feed("user", "test_follow")
    agg_feed = async_client.feed("aggregated", "test_follow")
    actor_id = random.randint(10, 100000)
    activity_data = {"actor": actor_id, "verb": "tweet", "object": 1}
    response = await feed.add_activity(activity_data)
    activity_id = response["id"]
    await agg_feed.follow(feed.slug, feed.user_id)

    response = await agg_feed.get(limit=3)
    activities = response["results"]
    activity = _get_first_aggregated_activity(activities)
    activity_id_found = activity["id"] if activity is not None else None
    assert activity["origin"] == feed.id
    assert activity_id_found == activity_id


@pytest.mark.asyncio
async def test_empty_followings(async_client):
    asocial = async_client.feed("user", "asocialpython")
    followings = await asocial.following()
    assert followings["results"] == []


@pytest.mark.asyncio
async def test_get_followings(async_client):
    social = async_client.feed("user", "psocial")
    await social.follow("user", "apy")
    await social.follow("user", "bpy")
    await social.follow("user", "cpy")
    followings = await social.following(offset=0, limit=2)
    assert len(followings["results"]) == 2
    assert followings["results"][0]["feed_id"] == social.id
    assert followings["results"][0]["target_id"] == "user:cpy"
    followings = await social.following(offset=1, limit=2)
    assert len(followings["results"]) == 2
    assert followings["results"][0]["feed_id"] == social.id
    assert followings["results"][0]["target_id"] == "user:bpy"


@pytest.mark.asyncio
async def test_empty_followers(async_client):
    asocial = async_client.feed("user", "asocialpython")
    followers = await asocial.followers()
    assert followers["results"] == []


@pytest.mark.asyncio
async def test_get_followers(async_client):
    social = async_client.feed("user", "psocial")
    spammy1 = async_client.feed("user", "spammy1")
    spammy2 = async_client.feed("user", "spammy2")
    spammy3 = async_client.feed("user", "spammy3")
    for feed in [spammy1, spammy2, spammy3]:
        await feed.follow("user", social.user_id)
    followers = await social.followers(offset=0, limit=2)
    assert len(followers["results"]) == 2
    assert followers["results"][0]["feed_id"] == spammy3.id
    assert followers["results"][0]["target_id"] == social.id
    followers = await social.followers(offset=1, limit=2)
    assert len(followers["results"]) == 2
    assert followers["results"][0]["feed_id"] == spammy2.id
    assert followers["results"][0]["target_id"] == social.id


@pytest.mark.asyncio
async def test_empty_do_i_follow(async_client):
    social = async_client.feed("user", "psocial")
    await social.follow("user", "apy")
    await social.follow("user", "bpy")
    followings = await social.following(feeds=["user:missingpy"])
    assert followings["results"] == []


@pytest.mark.asyncio
async def test_do_i_follow(async_client):
    social = async_client.feed("user", "psocial")
    await social.follow("user", "apy")
    await social.follow("user", "bpy")
    followings = await social.following(feeds=["user:apy"])
    assert len(followings["results"]) == 1
    assert followings["results"][0]["feed_id"] == social.id
    assert followings["results"][0]["target_id"] == "user:apy"


@pytest.mark.asyncio
async def test_update_activity_to_targets(user1):
    now = datetime.utcnow().isoformat()
    foreign_id = "user:1"
    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "foreign_id": foreign_id,
        "time": now,
        "to": ["user:1", "user:2"],
    }
    await user1.add_activity(activity_data)

    ret = await user1.update_activity_to_targets(
        foreign_id, now, new_targets=["user:3", "user:2"]
    )
    assert len(ret["activity"]["to"]) == 2
    assert "user:2" in ret["activity"]["to"]
    assert "user:3" in ret["activity"]["to"]

    ret = await user1.update_activity_to_targets(
        foreign_id,
        now,
        added_targets=["user:4", "user:5"],
        removed_targets=["user:3"],
    )
    assert len(ret["activity"]["to"]) == 3
    assert "user:2" in ret["activity"]["to"]
    assert "user:4" in ret["activity"]["to"]
    assert "user:5" in ret["activity"]["to"]


@pytest.mark.asyncio
async def test_get(user1):
    activity_data = {"actor": 1, "verb": "tweet", "object": 1}
    response1 = await user1.add_activity(activity_data)
    activity_id = response1["id"]
    activity_data = {"actor": 2, "verb": "add", "object": 2}
    response2 = await user1.add_activity(activity_data)
    activity_id_two = response2["id"]
    activity_data = {"actor": 3, "verb": "watch", "object": 2}
    response3 = await user1.add_activity(activity_data)
    activity_id_three = response3["id"]
    response = await user1.get(limit=2)
    activities = response["results"]
    # verify the first two results
    assert len(activities) == 2
    assert activities[0]["id"] == activity_id_three
    assert activities[1]["id"] == activity_id_two
    # try offset based
    response = await user1.get(limit=2, offset=1)
    activities = response["results"]
    assert activities[0]["id"] == activity_id_two
    # try id_lt based
    response = await user1.get(limit=2, id_lt=activity_id_two)
    activities = response["results"]
    assert activities[0]["id"] == activity_id


@pytest.mark.asyncio
async def test_get_not_marked_seen(async_client):
    notification_feed = async_client.feed("notification", "test_mark_seen")
    response = await notification_feed.get(limit=3)
    activities = response["results"]
    for activity in activities:
        assert not activity["is_seen"]


@pytest.mark.asyncio
async def test_mark_seen_on_get(async_client):
    notification_feed = async_client.feed("notification", "test_mark_seen")
    response = await notification_feed.get(limit=100)
    activities = response["results"]
    for activity in activities:
        await notification_feed.remove_activity(activity["id"])

        old_activities = [
            await notification_feed.add_activity(
                {"actor": 1, "verb": "tweet", "object": 1}
            ),
            await notification_feed.add_activity(
                {"actor": 2, "verb": "add", "object": 2}
            ),
            await notification_feed.add_activity(
                {"actor": 3, "verb": "watch", "object": 3}
            ),
        ]

        await notification_feed.get(
            mark_seen=[old_activities[0]["id"], old_activities[1]["id"]]
        )

        response = await notification_feed.get(limit=3)
        activities = response["results"]

        # is the seen state correct
        for activity in activities:
            # using a loop in case we're retrieving activities in a different
            # order than old_activities
            if old_activities[0]["id"] == activity["id"]:
                assert activity["is_seen"]
            if old_activities[1]["id"] == activity["id"]:
                assert activity["is_seen"]
            if old_activities[2]["id"] == activity["id"]:
                assert not activity["is_seen"]

        # see if the state properly resets after we add another activity
        await notification_feed.add_activity(
            {"actor": 3, "verb": "watch", "object": 3}
        )  # ['id']
        response = await notification_feed.get(limit=3)
        activities = response["results"]
        assert not activities[0]["is_seen"]
        assert len(activities[0]["activities"]) == 2


@pytest.mark.asyncio
async def test_mark_read_by_id(async_client):
    notification_feed = async_client.feed("notification", "py2")
    response = await notification_feed.get(limit=3)
    activities = response["results"]
    ids = []
    for activity in activities:
        ids.append(activity["id"])
        assert not activity["is_read"]
    ids = ids[:2]
    await notification_feed.get(mark_read=ids)
    response = await notification_feed.get(limit=3)
    activities = response["results"]
    for activity in activities:
        if activity["id"] in ids:
            assert activity["is_read"]
            assert not activity["is_seen"]


@pytest.mark.asyncio
async def test_api_key_exception():
    client = stream.connect(
        "5crf3bhfzesnMISSING",
        "tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su",
        use_async=True,
    )
    user1 = client.feed("user", "1")
    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "debug_example_undefined": "test",
    }
    with pytest.raises(ApiKeyException):
        await user1.add_activity(activity_data)


@pytest.mark.asyncio
async def test_complex_field(user1):
    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "participants": ["Tommaso", "Thierry"],
    }
    response = await user1.add_activity(activity_data)
    activity_id = response["id"]
    response = await user1.get(limit=1)
    activities = response["results"]
    assert activities[0]["id"] == activity_id
    assert activities[0]["participants"] == ["Tommaso", "Thierry"]


@pytest.mark.asyncio
async def test_uniqueness(user1):
    """
    In order for things to be considere unique they need:
    a.) The same time and activity data
    b.) The same time and foreign id
    """

    utcnow = datetime.now(tz=pytz.UTC)
    activity_data = {"actor": 1, "verb": "tweet", "object": 1, "time": utcnow}
    await user1.add_activity(activity_data)
    await user1.add_activity(activity_data)
    response = await user1.get(limit=2)
    activities = response["results"]
    assert_datetime_almost_equal(activities[0]["time"], utcnow)
    if len(activities) > 1:
        assert_clearly_not_equal(activities[1]["time"], utcnow)


@pytest.mark.asyncio
async def test_uniqueness_topic(flat3, topic, user1):
    """
    In order for things to be considere unique they need:
    a.) The same time and activity data, or
    b.) The same time and foreign id
    """
    # follow both the topic and the user
    await flat3.follow("topic", topic.user_id)
    await flat3.follow("user", user1.user_id)
    # add the same activity twice
    now = datetime.now(tzlocal())
    tweet = f"My Way {get_unique_postfix()}"
    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "time": now,
        "tweet": tweet,
    }
    await topic.add_activity(activity_data)
    await user1.add_activity(activity_data)
    # verify that flat3 contains the activity exactly once
    response = await flat3.get(limit=3)
    activity_tweets = [a.get("tweet") for a in response["results"]]
    assert activity_tweets.count(tweet) == 1


@pytest.mark.asyncio
async def test_uniqueness_foreign_id(user1):
    now = datetime.now(tzlocal())
    utcnow = now.astimezone(pytz.utc)

    activity_data = {
        "actor": 1,
        "verb": "tweet",
        "object": 1,
        "foreign_id": "tweet:11",
        "time": utcnow,
    }
    await user1.add_activity(activity_data)

    activity_data = {
        "actor": 2,
        "verb": "tweet",
        "object": 3,
        "foreign_id": "tweet:11",
        "time": utcnow,
    }
    await user1.add_activity(activity_data)
    response = await user1.get(limit=10)
    activities = response["results"]
    # the second post should have overwritten the first one (because they
    # had same id)

    assert len(activities) == 1
    assert activities[0]["object"] == "3"
    assert activities[0]["foreign_id"] == "tweet:11"
    assert_datetime_almost_equal(activities[0]["time"], utcnow)


@pytest.mark.asyncio
async def test_time_ordering(user2):
    """
    datetime.datetime.now(tz=pytz.utc) is our recommended approach
    so if we add an activity
    add one using time
    add another activity it should be in the right spot
    """

    # timedelta is used to "make sure" that ordering is known even though
    # server time is not
    custom_time = datetime.now(tz=pytz.utc) - timedelta(days=1)

    feed = user2
    for index, activity_time in enumerate([None, custom_time, None]):
        await _test_sleep(1)  # so times are a bit different
        activity_data = {
            "actor": 1,
            "verb": "tweet",
            "object": 1,
            "foreign_id": f"tweet:{index}",
            "time": activity_time,
        }
        await feed.add_activity(activity_data)

    response = await feed.get(limit=3)
    activities = response["results"]
    # the second post should have overwritten the first one (because they
    # had same id)
    assert activities[0]["foreign_id"] == "tweet:2"
    assert activities[1]["foreign_id"] == "tweet:0"
    assert activities[2]["foreign_id"] == "tweet:1"
    assert_datetime_almost_equal(activities[2]["time"], custom_time)


@pytest.mark.asyncio
async def test_missing_actor(user1):
    activity_data = {
        "verb": "tweet",
        "object": 1,
        "debug_example_undefined": "test",
    }
    try:
        await user1.add_activity(activity_data)
        raise ValueError("should have raised InputException")
    except InputException:
        pass


@pytest.mark.asyncio
async def test_follow_many(async_client):
    sources = [async_client.feed("user", str(i)).id for i in range(10)]
    targets = [async_client.feed("flat", str(i)).id for i in range(10)]
    feeds = [{"source": s, "target": t} for s, t in zip(sources, targets)]
    await async_client.follow_many(feeds)

    for target in targets:
        response = await async_client.feed(*target.split(":")).followers()
        follows = response["results"]
        assert len(follows) == 1
        assert follows[0]["feed_id"] in sources
        assert follows[0]["target_id"] == target

    for source in sources:
        response = await async_client.feed(*source.split(":")).following()
        follows = response["results"]
        assert len(follows) == 1
        assert follows[0]["feed_id"] in sources
        assert follows[0]["target_id"] == source


@pytest.mark.asyncio
async def test_follow_many_acl(async_client):
    sources = [async_client.feed("user", str(i)) for i in range(10)]
    # ensure every source is empty first
    for feed in sources:
        response = await feed.get(limit=100)
        activities = response["results"]
        for activity in activities:
            await feed.remove_activity(activity["id"])

    targets = [async_client.feed("flat", str(i)) for i in range(10)]
    # ensure every source is empty first
    for feed in targets:
        response = await feed.get(limit=100)
        activities = response["results"]
        for activity in activities:
            await feed.remove_activity(activity["id"])
    # add activity to each target feed
    activity = {
        "actor": "barry",
        "object": "09",
        "verb": "tweet",
        "time": datetime.utcnow().isoformat(),
    }
    for feed in targets:
        await feed.add_activity(activity)
        response = await feed.get(limit=5)
        assert len(response["results"]) == 1

    sources_id = [feed.id for feed in sources]
    targets_id = [target.id for target in targets]
    feeds = [{"source": s, "target": t} for s, t in zip(sources_id, targets_id)]

    await async_client.follow_many(feeds, activity_copy_limit=0)

    for feed in sources:
        response = await feed.get(limit=5)
        activities = response["results"]
        assert len(activities) == 0


@pytest.mark.asyncio
async def test_unfollow_many(async_client):
    unfollows = [
        {"source": "user:1", "target": "timeline:1"},
        {"source": "user:2", "target": "timeline:2", "keep_history": False},
    ]

    await async_client.unfollow_many(unfollows)
    unfollows.append({"source": "user:1", "target": 42})

    async def failing_unfollow():
        await async_client.unfollow_many(unfollows)

    with pytest.raises(InputException):
        await failing_unfollow()


@pytest.mark.asyncio
async def test_add_to_many(async_client):
    activity = {"actor": 1, "verb": "tweet", "object": 1, "custom": "data"}
    feeds = [async_client.feed("flat", str(i)).id for i in range(10, 20)]
    await async_client.add_to_many(activity, feeds)

    for feed in feeds:
        feed = async_client.feed(*feed.split(":"))
        response = await feed.get()
        assert response["results"][0]["custom"] == "data"


@pytest.mark.asyncio
async def test_get_activities_empty_ids(async_client):
    response = await async_client.get_activities(ids=[str(uuid1())])
    assert len(response["results"]) == 0


@pytest.mark.asyncio
async def test_get_activities_empty_foreign_ids(async_client):
    response = await async_client.get_activities(
        foreign_id_times=[("fid-x", datetime.utcnow())]
    )
    assert len(response["results"]) == 0


@pytest.mark.asyncio
async def test_get_activities_full(async_client):
    dt = datetime.utcnow()
    fid = "awesome-test"

    activity = {
        "actor": "barry",
        "object": "09",
        "verb": "tweet",
        "time": dt,
        "foreign_id": fid,
    }

    feed = async_client.feed("user", "test_get_activity")
    response = await feed.add_activity(activity)

    response = await async_client.get_activities(ids=[response["id"]])
    assert len(response["results"]) == 1
    foreign_id = response["results"][0]["foreign_id"]
    assert activity["foreign_id"] == foreign_id

    response = await async_client.get_activities(foreign_id_times=[(fid, dt)])
    assert len(response["results"]) == 1
    foreign_id = response["results"][0]["foreign_id"]
    assert activity["foreign_id"] == foreign_id


@pytest.mark.asyncio
async def test_get_activities_full_with_enrichment(async_client):
    dt = datetime.utcnow()
    fid = "awesome-test"

    actor = await async_client.users.add(str(uuid1()), data={"name": "barry"})
    activity = {
        "actor": async_client.users.create_reference(actor["id"]),
        "object": "09",
        "verb": "tweet",
        "time": dt,
        "foreign_id": fid,
    }

    feed = async_client.feed("user", "test_get_activity")
    activity = await feed.add_activity(activity)

    reaction1 = await async_client.reactions.add("like", activity["id"], "liker")
    reaction2 = await async_client.reactions.add("reshare", activity["id"], "sharer")

    def validate(response):
        assert len(response["results"]) == 1
        assert response["results"][0]["id"] == activity["id"]
        assert response["results"][0]["foreign_id"] == activity["foreign_id"]
        assert response["results"][0]["actor"]["data"]["name"] == "barry"
        latest_reactions = response["results"][0]["latest_reactions"]
        assert len(latest_reactions) == 2
        assert latest_reactions["like"][0]["id"] == reaction1["id"]
        assert latest_reactions["reshare"][0]["id"] == reaction2["id"]
        assert response["results"][0]["reaction_counts"] == {"like": 1, "reshare": 1}

    reactions = {"recent": True, "counts": True}
    validate(
        await async_client.get_activities(ids=[activity["id"]], reactions=reactions)
    )
    validate(
        await async_client.get_activities(
            foreign_id_times=[(fid, dt)], reactions=reactions
        )
    )


@pytest.mark.asyncio
async def test_get_activities_full_with_enrichment_and_reaction_kinds(async_client):
    dt = datetime.utcnow()
    fid = "awesome-test"

    actor = await async_client.users.add(str(uuid1()), data={"name": "barry"})
    activity = {
        "actor": async_client.users.create_reference(actor["id"]),
        "object": "09",
        "verb": "tweet",
        "time": dt,
        "foreign_id": fid,
    }

    feed = async_client.feed("user", "test_get_activity")
    activity = await feed.add_activity(activity)

    await async_client.reactions.add("like", activity["id"], "liker")
    await async_client.reactions.add("reshare", activity["id"], "sharer")
    await async_client.reactions.add("comment", activity["id"], "commenter")

    reactions = {"recent": True, "counts": True, "kinds": "like,comment"}
    response = await async_client.get_activities(
        ids=[activity["id"]], reactions=reactions
    )
    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == activity["id"]
    assert sorted(response["results"][0]["latest_reactions"].keys()) == [
        "comment",
        "like",
    ]

    assert response["results"][0]["reaction_counts"] == {"like": 1, "comment": 1}

    reactions = {
        "recent": True,
        "counts": True,
        "kinds": ["", "reshare   ", "comment\n"],
    }
    response = await async_client.get_activities(
        foreign_id_times=[(fid, dt)], reactions=reactions
    )
    assert len(response["results"]) == 1
    assert response["results"][0]["id"] == activity["id"]
    assert sorted(response["results"][0]["latest_reactions"].keys()) == [
        "comment",
        "reshare",
    ]
    assert response["results"][0]["reaction_counts"] == {"comment": 1, "reshare": 1}


@pytest.mark.asyncio
async def test_activity_partial_update(async_client):
    now = datetime.utcnow()
    feed = async_client.feed("user", uuid4())
    await feed.add_activity(
        {
            "actor": "barry",
            "object": "09",
            "verb": "tweet",
            "time": now,
            "foreign_id": "fid:123",
            "product": {"name": "shoes", "price": 9.99, "color": "blue"},
        }
    )
    response = await feed.get()
    activity = response["results"][0]

    to_set = {
        "product.name": "boots",
        "product.price": 7.99,
        "popularity": 1000,
        "foo": {"bar": {"baz": "qux"}},
    }
    to_unset = ["product.color"]

    # partial update by ID
    await async_client.activity_partial_update(
        id=activity["id"], set=to_set, unset=to_unset
    )
    response = await feed.get()
    updated = response["results"][0]
    expected = activity
    expected["product"] = {"name": "boots", "price": 7.99}
    expected["popularity"] = 1000
    expected["foo"] = {"bar": {"baz": "qux"}}
    assert updated == expected

    # partial update by foreign ID + time
    to_set = {"foo.bar.baz": 42, "popularity": 9000}
    to_unset = ["product.price"]
    await async_client.activity_partial_update(
        foreign_id=activity["foreign_id"],
        time=activity["time"],
        set=to_set,
        unset=to_unset,
    )
    response = await feed.get()
    updated = response["results"][0]
    expected["product"] = {"name": "boots"}
    expected["foo"] = {"bar": {"baz": 42}}
    expected["popularity"] = 9000
    assert updated == expected


@pytest.mark.asyncio
async def test_activities_partial_update(async_client):
    feed = async_client.feed("user", uuid4())
    await feed.add_activities(
        [
            {
                "actor": "barry",
                "object": "09",
                "verb": "tweet",
                "time": datetime.utcnow(),
                "foreign_id": "fid:123",
                "product": {"name": "shoes", "price": 9.99, "color": "blue"},
            },
            {
                "actor": "jerry",
                "object": "10",
                "verb": "tweet",
                "time": datetime.utcnow(),
                "foreign_id": "fid:456",
                "product": {"name": "shoes", "price": 9.99, "color": "blue"},
            },
            {
                "actor": "tommy",
                "object": "09",
                "verb": "tweet",
                "time": datetime.utcnow(),
                "foreign_id": "fid:789",
                "product": {"name": "shoes", "price": 9.99, "color": "blue"},
            },
        ]
    )
    response = await feed.get()
    activities = response["results"]

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
    await async_client.activities_partial_update(batch)
    response = await feed.get()
    updated = response["results"]
    expected = activities
    expected[0]["product"] = {"name": "shoes", "color": "purple"}
    expected[0]["custom"] = {"some": "extra data"}
    expected[2]["product"] = {"name": "shoes", "price": 9001, "color": "blue"}
    expected[2]["on_sale"] = True
    assert updated == expected

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
    await async_client.activities_partial_update(batch)
    response = await feed.get()
    updated = response["results"]

    expected[1]["product"] = {"price": 9.99, "color": "beeeeeeige"}
    expected[1]["custom"] = {"modified_by": "me"}
    del expected[2]["on_sale"]
    assert updated == expected


@pytest.mark.asyncio
async def test_reaction_add(async_client):
    await async_client.reactions.add(
        "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
    )


@pytest.mark.asyncio
async def test_reaction_add_to_target_feeds(async_client):
    r = await async_client.reactions.add(
        "superlike",
        "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4",
        "mike",
        data={"popularity": 50},
        target_feeds=["user:michelle"],
        target_feeds_extra_data={"popularity": 100},
    )
    assert r["data"]["popularity"] == 50
    response = await async_client.feed("user", "michelle").get(limit=1)
    a = response["results"][0]
    assert r["id"] in a["reaction"]
    assert a["verb"] == "superlike"
    assert a["popularity"] == 100

    child = await async_client.reactions.add_child(
        "superlike",
        r["id"],
        "rob",
        data={"popularity": 60},
        target_feeds=["user:michelle"],
        target_feeds_extra_data={"popularity": 200},
    )

    assert child["data"]["popularity"] == 60
    response = await async_client.feed("user", "michelle").get(limit=1)
    a = response["results"][0]
    assert child["id"] in a["reaction"]
    assert a["verb"] == "superlike"
    assert a["popularity"] == 200


@pytest.mark.asyncio
async def test_reaction_get(async_client):
    response = await async_client.reactions.add(
        "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
    )
    reaction = await async_client.reactions.get(response["id"])
    assert reaction["parent"] == ""
    assert reaction["data"] == {}
    assert reaction["latest_children"] == {}
    assert reaction["children_counts"] == {}
    assert reaction["activity_id"] == "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4"
    assert reaction["kind"] == "like"
    assert "created_at" in reaction
    assert "updated_at" in reaction
    assert "id" in reaction


@pytest.mark.asyncio
async def test_reaction_update(async_client):
    response = await async_client.reactions.add(
        "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
    )
    await async_client.reactions.update(response["id"], {"changed": True})


@pytest.mark.asyncio
async def test_reaction_delete(async_client):
    response = await async_client.reactions.add(
        "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
    )
    await async_client.reactions.delete(response["id"])


@pytest.mark.asyncio
async def test_reaction_add_child(async_client):
    response = await async_client.reactions.add(
        "like", "54a60c1e-4ee3-494b-a1e3-50c06acb5ed4", "mike"
    )
    await async_client.reactions.add_child("like", response["id"], "rob")


@pytest.mark.asyncio
async def test_reaction_filter_random(async_client):
    await async_client.reactions.filter(
        kind="like",
        reaction_id="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
        id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
    )
    await async_client.reactions.filter(
        activity_id="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
        id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b",
    )
    await async_client.reactions.filter(
        user_id="mike", id_lte="87a9eec0-fd5f-11e8-8080-80013fed2f5b"
    )


def _first_result_should_be(response, element):
    el = element.copy()
    el.pop("duration")
    assert len(response["results"]) == 1
    assert response["results"][0] == el


@pytest.mark.asyncio
async def test_reaction_filter(async_client):
    activity_id = str(uuid1())
    user = str(uuid1())

    response = await async_client.reactions.add("like", activity_id, user)
    child = await async_client.reactions.add_child("like", response["id"], user)
    reaction = await async_client.reactions.get(response["id"])

    response = await async_client.reactions.add("comment", activity_id, user)
    reaction_comment = await async_client.reactions.get(response["id"])

    r = await async_client.reactions.filter(reaction_id=reaction["id"])
    _first_result_should_be(r, child)

    r = await async_client.reactions.filter(
        kind="like", activity_id=activity_id, id_lte=reaction["id"]
    )
    _first_result_should_be(r, reaction)

    r = await async_client.reactions.filter(
        kind="like", user_id=user, id_lte=reaction["id"]
    )
    _first_result_should_be(r, reaction)

    r = await async_client.reactions.filter(kind="comment", activity_id=activity_id)
    _first_result_should_be(r, reaction_comment)


@pytest.mark.asyncio
async def test_user_add(async_client):
    await async_client.users.add(str(uuid1()))


@pytest.mark.asyncio
async def test_user_add_get_or_create(async_client):
    user_id = str(uuid1())
    r1 = await async_client.users.add(user_id)
    r2 = await async_client.users.add(user_id, get_or_create=True)
    assert r1["id"] == r2["id"]
    assert r1["created_at"] == r2["created_at"]
    assert r1["updated_at"] == r2["updated_at"]


@pytest.mark.asyncio
async def test_user_get(async_client):
    response = await async_client.users.add(str(uuid1()))
    user = await async_client.users.get(response["id"])
    assert user["data"] == {}
    assert "created_at" in user
    assert "updated_at" in user
    assert "id" in user


@pytest.mark.asyncio
async def test_user_get_with_follow_counts(async_client):
    response = await async_client.users.add(str(uuid1()))
    user = await async_client.users.get(response["id"], with_follow_counts=True)
    assert user["id"] == response["id"]
    assert "followers_count" in user
    assert "following_count" in user


@pytest.mark.asyncio
async def test_user_update(async_client):
    response = await async_client.users.add(str(uuid1()))
    await async_client.users.update(response["id"], {"changed": True})


@pytest.mark.asyncio
async def test_user_delete(async_client):
    response = await async_client.users.add(str(uuid1()))
    await async_client.users.delete(response["id"])


@pytest.mark.asyncio
async def test_collections_add(async_client):
    await async_client.collections.add(
        "items", {"data": 1}, id=str(uuid1()), user_id="tom"
    )


@pytest.mark.asyncio
async def test_collections_add_no_id(async_client):
    await async_client.collections.add("items", {"data": 1})


@pytest.mark.asyncio
async def test_collections_get(async_client):
    response = await async_client.collections.add("items", {"data": 1}, id=str(uuid1()))
    entry = await async_client.collections.get("items", response["id"])
    assert entry["data"] == {"data": 1}
    assert "created_at" in entry
    assert "updated_at" in entry
    assert "id" in entry


@pytest.mark.asyncio
async def test_collections_update(async_client):
    response = await async_client.collections.add("items", {"data": 1}, str(uuid1()))
    await async_client.collections.update(
        "items", response["id"], data={"changed": True}
    )
    entry = await async_client.collections.get("items", response["id"])
    assert entry["data"] == {"changed": True}


@pytest.mark.asyncio
async def test_collections_delete(async_client):
    response = await async_client.collections.add("items", {"data": 1}, str(uuid1()))
    await async_client.collections.delete("items", response["id"])


@pytest.mark.asyncio
async def test_feed_enrichment_collection(async_client):
    entry = await async_client.collections.add("items", {"name": "time machine"})
    entry.pop("duration")
    f = async_client.feed("user", "mike")
    activity_data = {
        "actor": "mike",
        "verb": "buy",
        "object": async_client.collections.create_reference(entry=entry),
    }
    await f.add_activity(activity_data)
    response = await f.get()
    assert set(activity_data.items()).issubset(set(response["results"][0].items()))
    enriched_response = await f.get(enrich=True)
    assert enriched_response["results"][0]["object"] == entry


@pytest.mark.asyncio
async def test_feed_enrichment_user(async_client):
    user = await async_client.users.add(str(uuid1()), {"name": "Mike"})
    user.pop("duration")
    f = async_client.feed("user", "mike")
    activity_data = {
        "actor": async_client.users.create_reference(user),
        "verb": "buy",
        "object": "time machine",
    }
    await f.add_activity(activity_data)
    response = await f.get()
    assert set(activity_data.items()).issubset(set(response["results"][0].items()))
    enriched_response = await f.get(enrich=True)
    assert enriched_response["results"][0]["actor"] == user


@pytest.mark.asyncio
async def test_feed_enrichment_own_reaction(async_client):
    f = async_client.feed("user", "mike")
    activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
    response = await f.add_activity(activity_data)
    reaction = await async_client.reactions.add("like", response["id"], "mike")
    reaction.pop("duration")
    enriched_response = await f.get(reactions={"own": True}, user_id="mike")
    assert enriched_response["results"][0]["own_reactions"]["like"][0] == reaction


@pytest.mark.asyncio
async def test_feed_enrichment_recent_reaction(async_client):
    f = async_client.feed("user", "mike")
    activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
    response = await f.add_activity(activity_data)
    reaction = await async_client.reactions.add("like", response["id"], "mike")
    reaction.pop("duration")
    enriched_response = await f.get(reactions={"recent": True})
    assert enriched_response["results"][0]["latest_reactions"]["like"][0] == reaction


@pytest.mark.asyncio
async def test_feed_enrichment_reaction_counts(async_client):
    f = async_client.feed("user", "mike")
    activity_data = {"actor": "mike", "verb": "buy", "object": "object"}
    response = await f.add_activity(activity_data)
    reaction = await async_client.reactions.add("like", response["id"], "mike")
    reaction.pop("duration")
    enriched_response = await f.get(reactions={"counts": True})
    assert enriched_response["results"][0]["reaction_counts"]["like"] == 1


@pytest.mark.asyncio
async def test_track_engagements(async_client):
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
    await async_client.track_engagements(engagements)


@pytest.mark.asyncio
async def test_track_impressions(async_client):
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
    await async_client.track_impressions(impressions)


@pytest.mark.asyncio
async def test_og(async_client):
    response = await async_client.og("https://google.com")
    assert "title" in response
    assert "description" in response


@pytest.mark.asyncio
async def test_follow_stats(async_client):
    uniq = uuid4()
    f = async_client.feed("user", uniq)
    await f.follow("user", uuid4())
    await f.follow("user", uuid4())
    await f.follow("user", uuid4())

    await async_client.feed("user", uuid4()).follow("user", uniq)
    await async_client.feed("timeline", uuid4()).follow("user", uniq)

    feed_id = "user:" + str(uniq)
    response = await async_client.follow_stats(feed_id)
    result = response["results"]
    assert result["following"]["count"] == 3
    assert result["followers"]["count"] == 2

    response = await async_client.follow_stats(
        feed_id, followers_slugs=["timeline"], following_slugs=["timeline"]
    )
    result = response["results"]
    assert result["following"]["count"] == 0
    assert result["followers"]["count"] == 1

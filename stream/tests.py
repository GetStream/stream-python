from dateutil.tz import tzlocal
import stream
import time
from stream.exceptions import ApiKeyException, InputException
import random
from unittest.case import TestCase

import os
import datetime
from stream import serializer
from requests.exceptions import ConnectionError, MissingSchema
from urlparse import urlparse


def connect_debug():
    return stream.connect(
        'ahj2ndz7gsan',
        'gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy',
        location='us-east',
        timeout=10
    )

random_postfix = str(int(time.time())) + str(random.randint(0, 1000))
client = connect_debug()


def getfeed(feed_slug, user_id):
    '''
    Adds the random postfix to the user id
    '''
    return client.feed(feed_slug, user_id + random_postfix)

user1 = getfeed('user', '1')
user2 = getfeed('user', '2')
aggregated2 = getfeed('aggregated', '2')
aggregated3 = getfeed('aggregated', '3')
topic1 = getfeed('topic', '1')
flat3 = getfeed('flat', '3')


class ClientTest(TestCase):

    def setUp(self):
        # DEBUG account details
        self.c = client
        self.user1 = user1
        self.user2 = user2
        self.aggregated2 = aggregated2
        self.aggregated3 = aggregated3
        self.topic1 = topic1
        self.flat3 = flat3

    def test_heroku(self):
        url = 'https://thierry:pass@getstream.io/?app_id=1'
        os.environ['STREAM_URL'] = url
        client = stream.connect()
        self.assertEqual(client.api_key, 'thierry')
        self.assertEqual(client.api_secret, 'pass')
        self.assertEqual(client.app_id, '1')

    def test_heroku_no_location(self):
        url = 'https://bvt88g4kvc63:twc5ywfste5bm2ngqkzs7ukxk3pn96yweghjrxcmcrarnt3j4dqj3tucbhym5wfd@getstream.io/?app_id=669'
        os.environ['STREAM_URL'] = url
        client = stream.connect()
        self.assertEqual(client.api_key, 'bvt88g4kvc63')
        self.assertEqual(
            client.api_secret, 'twc5ywfste5bm2ngqkzs7ukxk3pn96yweghjrxcmcrarnt3j4dqj3tucbhym5wfd')
        self.assertEqual(client.app_id, '669')
        self.assertEqual(
            client.base_url, 'https://api.getstream.io/api/')
        
    def test_heroku_location(self):
        url = 'https://ahj2ndz7gsan:gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy@us-east.getstream.io/?app_id=1'
        os.environ['STREAM_URL'] = url
        client = stream.connect()
        self.assertEqual(client.api_key, 'ahj2ndz7gsan')
        self.assertEqual(
            client.api_secret, 'gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy')
        self.assertEqual(
            client.base_url, 'https://us-east-api.getstream.io/api/')
        self.assertEqual(client.app_id, '1')

    def test_heroku_overwrite(self):
        url = 'https://thierry:pass@getstream.io/?app_id=1'
        os.environ['STREAM_URL'] = url
        client = stream.connect('a', 'b', 'c')
        self.assertEqual(client.api_key, 'a')
        self.assertEqual(client.api_secret, 'b')
        self.assertEqual(client.app_id, 'c')
        
    def test_location_support(self):
        client = stream.connect('a', 'b', 'c', location='us-east')
        full_location = 'https://us-east-api.getstream.io/api/'
        self.assertEqual(client.location, 'us-east')
        self.assertEqual(client.base_url, full_location)
        # test a wrong location
        client = stream.connect('a', 'b', 'c', location='nonexistant')
        def get_feed():
            client.feed('user', '1').get()
        self.assertRaises(ConnectionError, get_feed)
        
    def test_invalid_feed_values(self):
        def invalid_feed_slug():
            client.feed('user:', '1')
        self.assertRaises(ValueError, invalid_feed_slug)
        
        def invalid_user_id():
            client.feed('user:', '1-a')
        self.assertRaises(ValueError, invalid_user_id)
            
        def invalid_follow_feed_slug():
            self.user1.follow('user:', '1')
        self.assertRaises(ValueError, invalid_follow_feed_slug)
            
        def invalid_follow_user_id():
            self.user1.follow('user', '1-:a')
        self.assertRaises(ValueError, invalid_follow_user_id)

    def test_token_retrieval(self):
        self.user1.token

    def test_add_activity(self):
        feed = getfeed('user', 'py1')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        response = feed.add_activity(activity_data)
        activity_id = response['id']
        activities = feed.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)

    def test_add_activity_to(self):
        # test for sending an activities to the team feed using to
        feeds = ['user', 'teamy', 'team_follower']
        user_feed, team_feed, team_follower_feed = map(lambda x: getfeed('user', x), feeds)
        team_follower_feed.follow(team_feed.slug, team_feed.user_id)
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1,
            'to': [team_feed.id]
        }
        response = user_feed.add_activity(activity_data)
        activity_id = response['id']
        time.sleep(2)
        # see if the new activity is also in the team feed
        activities = team_feed.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)
        self.assertEqual(activities[0]['origin'], None)
        # see if the fanout process also works
        activities = team_follower_feed.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)
        self.assertEqual(activities[0]['origin'], team_feed.id)
        # and validate removing also works
        user_feed.remove_activity(response['id'])
        # check the user pyto feed
        activities = team_feed.get(limit=1)['results']
        self.assertFirstActivityIDNotEqual(activities, activity_id)
        # and the flat feed
        activities = team_follower_feed.get(limit=1)['results']
        self.assertFirstActivityIDNotEqual(activities, activity_id)
        
    def assertFirstActivityIDEqual(self, activities, correct_activity_id):
        activity_id = None
        if activities:
            activity_id = activities[0]['id']
        self.assertEqual(activity_id, correct_activity_id)
    
    def assertFirstActivityIDNotEqual(self, activities, correct_activity_id):
        activity_id = None
        if activities:
            activity_id = activities[0]['id']
        self.assertNotEqual(activity_id, correct_activity_id)
        
    def test_remove_activity(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.user1.remove_activity(activity_id)
        activities = self.user1.get(limit=1)['results']
        self.assertNotEqual(activities[0]['id'], activity_id)

    def test_remove_activity_by_foreign_id(self):
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1, 'foreign_id': 'tweet:10'}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.user1.remove_activity(foreign_id='tweet:10')
        activities = self.user1.get(limit=1)['results']
        self.assertNotEqual(activities[0]['id'], activity_id)
        # verify this doesnt raise an error, but fails silently
        self.user1.remove_activity(foreign_id='tweet:unknowandmissing')

    def test_add_activities(self):
        activity_data = [
            {'actor': 1, 'verb': 'tweet', 'object': 1},
            {'actor': 2, 'verb': 'watch', 'object': 2},
        ]
        response = self.user1.add_activities(activity_data)
        activity_ids = [a['id'] for a in response['activities']]
        activities = self.user1.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])

    def test_add_activities_to(self):
        to = [getfeed('user', 'pyto2').id, getfeed('user', 'pyto3').id]
        activity_data = [
            {'actor': 1, 'verb': 'tweet', 'object': 1, 'to': to},
            {'actor': 2, 'verb': 'watch', 'object': 2, 'to': to},
        ]
        response = self.user1.add_activities(activity_data)
        activity_ids = [a['id'] for a in response['activities']]
        activities = self.user1.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])
        # test first target
        feed = getfeed('user', 'pyto2')
        activities = feed.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])
        # test second target
        feed = getfeed('user', 'pyto3')
        activities = feed.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])

    def test_follow_and_source(self):
        feed = getfeed('user', 'test_follow')
        agg_feed = getfeed('aggregated', 'test_follow')
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = feed.add_activity(activity_data)['id']
        agg_feed.follow(feed.slug, feed.user_id)
        time.sleep(10)
        activities = agg_feed.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity['origin'], feed.id)
        self.assertEqual(activity_id_found, activity_id)
        
    def test_follow_and_delete(self):
        user_feed = getfeed('user', 'test_follow')
        agg_feed = getfeed('aggregated', 'test_follow')
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = user_feed.add_activity(activity_data)['id']
        agg_feed.follow(user_feed.slug, user_feed.user_id)
        user_feed.remove_activity(activity_id)
        time.sleep(2)
        for x in range(5):
            activities = agg_feed.get(limit=3)['results']
            activity = self._get_first_aggregated_activity(activities)
            activity_id_found = activity['id'] if activity is not None else None
            self.assertNotEqual(activity_id_found, activity_id)
            time.sleep(1)

    def test_follow_private(self):
        feed = getfeed('secret', 'py1')
        agg_feed = getfeed('aggregated', 'test_follow_private')
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = feed.add_activity(activity_data)['id']
        agg_feed.follow(feed.slug, feed.user_id)
        time.sleep(10)
        activities = agg_feed.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

    def test_flat_follow(self):
        feed = getfeed('user', 'test_flat_follow')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = feed.add_activity(activity_data)['id']
        self.flat3.follow(feed.slug, feed.user_id)
        time.sleep(10)
        activities = self.flat3.get(limit=3)['results']
        activity = self._get_first_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

    def test_flat_follow_no_copy(self):
        feed = getfeed('user', 'test_flat_follow_no_copy')
        follower = getfeed('flat', 'test_flat_follow_no_copy')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        feed.add_activity(activity_data)['id']
        follower.follow(feed.slug, feed.user_id, activity_copy_limit=0)
        time.sleep(10)
        activities = follower.get(limit=3)['results']
        self.assertEqual(activities, [])
        
    def test_flat_follow_copy_one(self):
        feed = getfeed('user', 'test_flat_follow_copy_one')
        follower = getfeed('flat', 'test_flat_follow_copy_one')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1, 'foreign_id': 'test:1'}
        feed.add_activity(activity_data)['id']
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1, 'foreign_id': 'test:2'}
        feed.add_activity(activity_data)['id']
        follower.follow(feed.slug, feed.user_id, activity_copy_limit=1)
        time.sleep(5)
        activities = follower.get(limit=3)['results']
        # verify we get the latest activity
        self.assertEqual(activities[0]['foreign_id'], 'test:2')

    def _get_first_aggregated_activity(self, activities):
        try:
            return activities[0]['activities'][0]
        except IndexError as e:
            pass

    def _get_first_activity(self, activities):
        try:
            return activities[0]
        except IndexError as e:
            pass

    def test_unfollow(self):
        f = getfeed('user', 'asocialpython').id.split(':')

    def test_empty_followings(self):
        asocial = getfeed('user', 'asocialpython')
        followings = asocial.following()
        self.assertEqual(followings['results'], [])

    def test_get_followings(self):
        social = getfeed('user', 'psocial')
        social.follow('user', 'apy')
        social.follow('user', 'bpy')
        social.follow('user', 'cpy')
        followings = social.following(offset=0, limit=2)
        self.assertEqual(len(followings['results']), 2)
        self.assertEqual(followings['results'][0]['feed_id'], social.id)
        self.assertEqual(followings['results'][0]['target_id'], 'user:cpy')
        followings = social.following(offset=1, limit=2)
        self.assertEqual(len(followings['results']), 2)
        self.assertEqual(followings['results'][0]['feed_id'], social.id)
        self.assertEqual(followings['results'][0]['target_id'], 'user:bpy')

    def test_empty_followers(self):
        asocial = getfeed('user', 'asocialpython')
        followers = asocial.followers()
        self.assertEqual(len(followers['results']), 0)
        self.assertEqual(followers['results'], [])

    def test_get_followers(self):
        social = getfeed('user', 'psocial')
        spammy1 = getfeed('user', 'spammy1')
        spammy2 = getfeed('user', 'spammy2')
        spammy3 = getfeed('user', 'spammy3')
        for feed in [spammy1, spammy2, spammy3]:
            feed.follow('user', social.user_id)
        followers = social.followers(offset=0, limit=2)
        self.assertEqual(len(followers['results']), 2)
        self.assertEqual(followers['results'][0]['feed_id'], spammy3.id)
        self.assertEqual(followers['results'][0]['target_id'], social.id)
        followers = social.followers(offset=1, limit=2)
        self.assertEqual(len(followers['results']), 2)
        self.assertEqual(followers['results'][0]['feed_id'], spammy2.id)
        self.assertEqual(followers['results'][0]['target_id'], social.id)

    def test_empty_do_i_follow(self):
        social = getfeed('user', 'psocial')
        social.follow('user', 'apy')
        social.follow('user', 'bpy')
        followings = social.following(feeds=['user:missingpy'])
        self.assertEqual(len(followings['results']), 0)
        self.assertEqual(followings['results'], [])

    def test_do_i_follow(self):
        social = getfeed('user', 'psocial')
        social.follow('user', 'apy')
        social.follow('user', 'bpy')
        followings = social.following(feeds=['user:apy'])
        self.assertEqual(len(followings['results']), 1)
        self.assertEqual(followings['results'][0]['feed_id'], social.id)
        self.assertEqual(followings['results'][0]['target_id'], 'user:apy')

    def test_get(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        activity_data = {'actor': 2, 'verb': 'add', 'object': 2}
        activity_id_two = self.user1.add_activity(activity_data)['id']
        activity_data = {'actor': 3, 'verb': 'watch', 'object': 2}
        activity_id_three = self.user1.add_activity(activity_data)['id']
        activities = self.user1.get(limit=2)['results']
        # verify the first two results
        self.assertEqual(len(activities), 2)
        self.assertEqual(activities[0]['id'], activity_id_three)
        self.assertEqual(activities[1]['id'], activity_id_two)
        # try offset based
        activities = self.user1.get(limit=2, offset=1)['results']
        self.assertEqual(activities[0]['id'], activity_id_two)
        # try id_lt based
        activities = self.user1.get(limit=2, id_lt=activity_id_two)['results']
        self.assertEqual(activities[0]['id'], activity_id)

    def test_mark_read(self):
        notification_feed = getfeed('notification', 'py3')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        notification_feed.add_activity(activity_data)
        activity_data = {'actor': 2, 'verb': 'add', 'object': 2}
        notification_feed.add_activity(activity_data)
        activity_data = {'actor': 3, 'verb': 'watch', 'object': 2}
        notification_feed.add_activity(activity_data)
        activities = notification_feed.get(limit=3)['results']
        for activity in activities:
            self.assertFalse(activity['is_read'])
        activities = notification_feed.get(mark_read=True)['results']
        activities = notification_feed.get(limit=2)['results']
        self.assertTrue(activities[0]['is_read'])
        self.assertTrue(activities[1]['is_read'])
            
    def test_mark_seen(self):
        notification_feed = getfeed('notification', 'test_mark_seen')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        notification_feed.add_activity(activity_data)
        activity_data = {'actor': 2, 'verb': 'add', 'object': 2}
        notification_feed.add_activity(activity_data)
        activity_data = {'actor': 3, 'verb': 'watch', 'object': 3}
        notification_feed.add_activity(activity_data)

        activities = notification_feed.get(limit=3)['results']
        for activity in activities:
            self.assertFalse(activity['is_seen'])
            
        activities = notification_feed.get(limit=3)['results']
        notification_feed.get(mark_seen=[activities[0]['id'], activities[1]['id']])['results']
        activities = notification_feed.get(limit=3)['results']
        # is the seen state correct
        self.assertTrue(activities[0]['is_seen'])
        self.assertTrue(activities[1]['is_seen'])
        self.assertFalse(activities[2]['is_seen'])
        # see if the state properly resets after we add another activity
        activity_data = {'actor': 3, 'verb': 'watch', 'object': 3}
        notification_feed.add_activity(activity_data)['id']
        activities = notification_feed.get(limit=3)['results']
        self.assertFalse(activities[0]['is_seen'])
        self.assertEqual(len(activities[0]['activities']), 2)

    def test_mark_read_by_id(self):
        notification_feed = getfeed('notification', 'py2')
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        notification_feed.add_activity(activity_data)['id']
        activity_data = {'actor': 2, 'verb': 'add', 'object': 2}
        notification_feed.add_activity(activity_data)['id']
        activity_data = {'actor': 3, 'verb': 'watch', 'object': 2}
        notification_feed.add_activity(activity_data)['id']
        activities = notification_feed.get(limit=3)['results']
        ids = []
        for activity in activities:
            ids.append(activity['id'])
            self.assertFalse(activity['is_read'])
        ids = ids[:2]
        notification_feed.get(mark_read=ids)
        activities = notification_feed.get(limit=3)['results']
        for activity in activities:
            if activity['id'] in ids:
                self.assertTrue(activity['is_read'])
                self.assertFalse(activity['is_seen'])

    def test_api_key_exception(self):
        self.c = stream.connect(
            '5crf3bhfzesnMISSING',
            'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
        )
        self.user1 = self.c.feed('user', '1')
        activity_data = {'actor': 1, 'verb': 'tweet',
                         'object': 1, 'debug_example_undefined': 'test'}
        self.assertRaises(ApiKeyException, lambda:
                          self.user1.add_activity(activity_data))

    def test_complex_field(self):
        activity_data = {'actor': 1, 'verb': 'tweet',
                         'object': 1, 'participants': ['Tommaso', 'Thierry']}
        response = self.user1.add_activity(activity_data)
        activity_id = response['id']
        activities = self.user1.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)
        self.assertEqual(activities[0]['participants'], ['Tommaso', 'Thierry'])

    def assertDatetimeAlmostEqual(self, a, b):
        difference = abs(a - b)
        if difference > datetime.timedelta(milliseconds=1):
            self.assertEqual(a, b)

    def assertClearlyNotEqual(self, a, b):
        difference = abs(a - b)
        if difference < datetime.timedelta(milliseconds=1):
            raise ValueError('the dates are too close')

    def test_uniqueness(self):
        '''
        In order for things to be considere unique they need:
        a.) The same time and activity data
        b.) The same time and foreign id
        '''
        from pprint import pprint
        utcnow = datetime.datetime.utcnow()
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1, 'time': utcnow}
        response = self.user1.add_activity(activity_data)
        response = self.user1.add_activity(activity_data)
        activities = self.user1.get(limit=2)['results']
        self.assertDatetimeAlmostEqual(activities[0]['time'], utcnow)
        if (len(activities) > 1):
            self.assertClearlyNotEqual(activities[1]['time'], utcnow)

    def test_uniqueness_topic(self):
        '''
        In order for things to be considere unique they need:
        a.) The same time and activity data, or
        b.) The same time and foreign id
        '''
        # follow both the topic and the user
        self.flat3.follow('topic', self.topic1.user_id)
        self.flat3.follow('user', self.user1.user_id)
        # add the same activity twice
        now = datetime.datetime.now(tzlocal())
        tweet = 'My Way %s' % random_postfix
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1, 'time': now, 'tweet': tweet}
        self.topic1.add_activity(activity_data)
        self.user1.add_activity(activity_data)
        # verify that flat3 contains the activity exactly once
        response = self.flat3.get(limit=3)
        activity_tweets = [a.get('tweet') for a in response['results']]
        self.assertEqual(activity_tweets.count(tweet), 1)

    def test_uniqueness_foreign_id(self):
        now = datetime.datetime.now(tzlocal())
        utcnow = (now - now.utcoffset()).replace(tzinfo=None)
        activity_data = {'actor': 1, 'verb': 'tweet',
                         'object': 1, 'foreign_id': 'tweet:11', 'time': now}
        response = self.user1.add_activity(activity_data)
        activity_data = {'actor': 2, 'verb': 'tweet',
                         'object': 3, 'foreign_id': 'tweet:11', 'time': now}
        response = self.user1.add_activity(activity_data)
        activities = self.user1.get(limit=2)['results']
        # the second post should have overwritten the first one (because they
        # had same id)
        self.assertEqual(activities[0]['object'], '3')
        self.assertEqual(activities[0]['foreign_id'], 'tweet:11')
        self.assertDatetimeAlmostEqual(activities[0]['time'], utcnow)
        self.assertNotEqual(activities[1]['foreign_id'], 'tweet:11')

    def test_time_ordering(self):
        '''
        datetime.datetime.utcnow() is our recommended approach
        so if we add an activity
        add one using time
        add another activity it should be in the right spot
        '''
        now = datetime.datetime.utcnow
        feed = self.user2
        for index, activity_time in enumerate([None, now, None]):
            time.sleep(1)
            if activity_time is not None:
                activity_time = activity_time()
                middle = activity_time
            activity_data = {'actor': 1, 'verb': 'tweet',
                             'object': 1, 'foreign_id': 'tweet:%s' % index, 'time': activity_time}
            feed.add_activity(activity_data)

        activities = feed.get(limit=3)['results']
        # the second post should have overwritten the first one (because they
        # had same id)
        self.assertEqual(activities[0]['foreign_id'], 'tweet:2')
        self.assertEqual(activities[1]['foreign_id'], 'tweet:1')
        self.assertEqual(activities[2]['foreign_id'], 'tweet:0')
        self.assertDatetimeAlmostEqual(activities[1]['time'], middle)

    def test_missing_actor(self):
        activity_data = {'verb': 'tweet', 'object':
                         1, 'debug_example_undefined': 'test'}
        doit = lambda: self.user1.add_activity(activity_data)
        try:
            doit()
            raise ValueError('should have raised InputException')
        except InputException as e:
            pass

    def test_wrong_feed_spec(self):
        self.c = stream.connect(
            '5crf3bhfzesnMISSING',
            'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
        )
        self.assertRaises(TypeError, lambda: getfeed('user1'))

    def test_serialization(self):
        today = datetime.date.today()
        now = datetime.datetime.now()
        data = dict(
            string='string', float=0.1, int=1, date=today, datetime=now)
        serialized = serializer.dumps(data)
        loaded = serializer.loads(serialized)
        self.assertEqual(data, loaded)

    def test_signed_request_post(self):
        self.c._make_signed_request('post', 'test/auth/digest/', {}, {})

    def test_signed_request_get(self):
        self.c._make_signed_request('post', 'test/auth/digest/', {}, {})

    def test_follow_many(self):
        sources = [getfeed('user', str(i)).id for i in range(10)]
        targets = [getfeed('flat', str(i)).id for i in range(10)]
        feeds = [{'source': s, 'target': t} for s,t in zip(sources, targets)]
        self.c.follow_many(feeds)

        for target in targets:
            follows = self.c.feed(*target.split(':')).followers()['results']
            self.assertEqual(len(follows), 1)
            self.assertIn(follows[0]['feed_id'], sources)
            self.assertEqual(follows[0]['target_id'], target)

        for source in sources:
            follows = self.c.feed(*source.split(':')).following()['results']
            self.assertEqual(len(follows), 1)
            self.assertEqual(follows[0]['feed_id'], source)
            self.assertIn(follows[0]['target_id'], targets)

    def test_add_to_many(self):
        activity = {'actor': 1, 'verb': 'tweet', 'object': 1, 'custom': 'data'}
        feeds = [getfeed('flat', str(i)).id for i in range(10, 20)]
        self.c.add_to_many(activity, feeds)

        for feed in feeds:
            feed = self.c.feed(*feed.split(':'))
            self.assertEqual(feed.get()['results'][0]['custom'], 'data')
            
    def test_create_email_redirect(self):
        expected_parts = ['https://analytics.getstream.io/analytics/redirect/',
            'auth_type=jwt',
            'url=http%3A%2F%2Fgoogle.com%2F%3Fa%3Db%26c%3Dd',
            'api_key=ahj2ndz7gsan',
            'authorization=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY3Rpb24iOiIqIiwidXNlcl9pZCI6InRvbW1hc28iLCJyZXNvdXJjZSI6InJlZGlyZWN0X2FuZF90cmFjayJ9.pQ2cBmC7l0WGP9LP7RrvLEbtrw8YWcFtjOqSfoSr2s0',
            'events=%5B%7B%22foreign_ids%22%3A+%5B%22tweet%3A1%22%2C+%22tweet%3A2%22%2C+%22tweet%3A3%22%2C+%22tweet%3A4%22%2C+%22tweet%3A5%22%5D%2C+%22feed_id%22%3A+%22user%3Aglobal%22%2C+%22user_id%22%3A+%22tommaso%22%2C+%22location%22%3A+%22email%22%7D%2C+%7B%22user_id%22%3A+%22tommaso%22%2C+%22label%22%3A+%22click%22%2C+%22feed_id%22%3A+%22user%3Aglobal%22%2C+%22location%22%3A+%22email%22%2C+%22position%22%3A+3%2C+%22foreign_id%22%3A+%22tweet%3A1%22%7D%5D',
        ]
        engagement = {'foreign_id': 'tweet:1', 'label': 'click', 'position': 3, 'user_id': 'tommaso', 'location': 'email', 'feed_id': 'user:global'}
        impression = {'foreign_ids': ['tweet:1', 'tweet:2', 'tweet:3', 'tweet:4', 'tweet:5'], 'user_id':
                      'tommaso', 'location': 'email', 'feed_id': 'user:global'}
        events = [impression, engagement]
        target_url = 'http://google.com/?a=b&c=d'
        user_id = 'tommaso'
        redirect_url = self.c.create_redirect_url(target_url, user_id, events)

        for part in expected_parts:
            if part not in redirect_url:
                raise ValueError('didnt find %s in url \n %s' % (part, redirect_url))
            
    def test_email_redirect_invalid_target(self):
        engagement = {'foreign_id': 'tweet:1', 'label': 'click', 'position': 3, 'user_id': 'tommaso', 'location': 'email', 'feed_id': 'user:global'}
        impression = {'foreign_ids': ['tweet:1', 'tweet:2', 'tweet:3', 'tweet:4', 'tweet:5'], 'user_id':
                      'tommaso', 'location': 'email', 'feed_id': 'user:global'}
        events = [impression, engagement]
        # no protocol specified, this should raise an error
        target_url = 'google.com'
        user_id = 'tommaso'
        create_redirect = lambda : self.c.create_redirect_url(target_url, user_id, events)
        self.assertRaises(MissingSchema, create_redirect)
        
        
        
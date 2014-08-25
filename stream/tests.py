from dateutil.tz import tzlocal
import stream
import time
from stream.exceptions import ApiKeyException, InputException,\
    CustomFieldException
import random
from unittest.case import TestCase

import os
import datetime
from stream import serializer


def connect_debug():
    return stream.connect(
        u'ahj2ndz7gsan',
        u'gthc2t9gh7pzq52f6cky8w4r4up9dr6rju9w3fjgmkv6cdvvav2ufe5fv7e2r9qy'
    )

client = connect_debug()
user1 = client.feed('user:1')
aggregated2 = client.feed('aggregated:2')
aggregated3 = client.feed('aggregated:3')
topic1 = client.feed('topic:1')
flat3 = client.feed('flat:3')


class ClientTest(TestCase):

    def setUp(self):
        # DEBUG account details
        self.c = client
        self.user1 = user1
        self.aggregated2 = aggregated2
        self.aggregated3 = aggregated3
        self.topic1 = topic1
        self.flat3 = flat3

    def test_heroku(self):
        url = 'https://thierry:pass@getstream.io/?site=1'
        os.environ['STREAM_URL'] = url
        client = stream.connect()
        self.assertEqual(client.api_key, 'thierry')
        self.assertEqual(client.api_secret, 'pass')
        self.assertEqual(client.site_id, '1')

    def test_heroku_overwrite(self):
        url = 'https://thierry:pass@getstream.io/?site=1'
        os.environ['STREAM_URL'] = url
        client = stream.connect('a', 'b', 'c')
        self.assertEqual(client.api_key, 'a')
        self.assertEqual(client.api_secret, 'b')
        self.assertEqual(client.site_id, 'c')

    def test_token_retrieval(self):
        token = self.user1.token

    def test_add_activity(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        response = self.user1.add_activity(activity_data)
        activity_id = response['id']
        activities = self.user1.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)

    def test_add_activity_to(self):
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1,
            'to': ['user:pyto1']
        }
        response = self.user1.add_activity(activity_data)
        feed = client.feed('user:pyto1')
        activity_id = response['id']
        activities = feed.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)

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
        to = ['user:pyto2', 'user:pyto3']
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
        feed = client.feed('user:pyto2')
        activities = feed.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])
        # test second target
        feed = client.feed('user:pyto3')
        activities = feed.get(limit=2)['results']
        get_activity_ids = [a['id'] for a in activities]
        self.assertEqual(get_activity_ids, activity_ids[::-1])

    def test_follow(self):
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.aggregated2.follow('user:1')
        time.sleep(10)
        activities = self.aggregated2.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

    def test_follow_private(self):
        feed = client.feed('secret:py1')
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = feed.add_activity(activity_data)['id']
        self.aggregated2.follow('secret:py1')
        time.sleep(10)
        activities = self.aggregated2.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

    def test_flat_follow(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.flat3.follow('user:1')
        time.sleep(10)
        activities = self.flat3.get(limit=3)['results']
        activity = self._get_first_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

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
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.aggregated3.follow('user:1')
        self.aggregated3.unfollow('user:1')
        time.sleep(5)
        activities = self.aggregated3.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertNotEqual(activity_id_found, activity_id)

    def test_empty_followings(self):
        asocial = client.feed('user:asocialpython')
        followings = asocial.following()
        self.assertEqual(followings['results'], [])

    def test_get_followings(self):
        social = client.feed('user:psocial')
        social.follow('user:apy')
        social.follow('user:bpy')
        social.follow('user:cpy')
        followings = social.following(offset=0, limit=2)
        self.assertEqual(len(followings['results']), 2)
        self.assertEqual(followings['results'][0]['feed_id'], 'user:psocial')
        self.assertEqual(followings['results'][0]['target_id'], 'user:cpy')
        followings = social.following(offset=1, limit=2)
        self.assertEqual(len(followings['results']), 2)
        self.assertEqual(followings['results'][0]['feed_id'], 'user:psocial')
        self.assertEqual(followings['results'][0]['target_id'], 'user:bpy')

    def test_empty_followers(self):
        asocial = client.feed('user:asocialpython')
        followers = asocial.following()
        self.assertEqual(len(followers['results']), 0)
        self.assertEqual(followers['results'], [])

    def test_get_followers(self):
        social = client.feed('user:psocial')
        client.feed('user:spammy1').follow('user:psocial')
        client.feed('user:spammy2').follow('user:psocial')
        client.feed('user:spammy3').follow('user:psocial')
        followers = social.followers(offset=0, limit=2)
        self.assertEqual(len(followers['results']), 2)
        self.assertEqual(followers['results'][0]['feed_id'], 'user:spammy3')
        self.assertEqual(followers['results'][0]['target_id'], 'user:psocial')
        followers = social.followers(offset=1, limit=2)
        self.assertEqual(len(followers['results']), 2)
        self.assertEqual(followers['results'][0]['feed_id'], 'user:spammy2')
        self.assertEqual(followers['results'][0]['target_id'], 'user:psocial')

    def test_empty_do_i_follow(self):
        social = client.feed('user:psocial')
        social.follow('user:apy')
        social.follow('user:bpy')
        followings = social.following(feeds=['user:missingpy'])
        self.assertEqual(len(followings['results']), 0)
        self.assertEqual(followings['results'], [])

    def test_do_i_follow(self):
        social = client.feed('user:psocial')
        social.follow('user:apy')
        social.follow('user:bpy')
        followings = social.following(feeds=['user:apy'])
        self.assertEqual(len(followings['results']), 1)
        self.assertEqual(followings['results'][0]['feed_id'], 'user:psocial')
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

    def test_api_key_exception(self):
        self.c = stream.connect(
            '5crf3bhfzesnMISSING',
            'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
        )
        self.user1 = self.c.feed('user:1')
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
        utcnow = datetime.datetime.utcnow()
        activity_data = {
            'actor': 1, 'verb': 'tweet', 'object': 1, 'time': utcnow}
        response = self.user1.add_activity(activity_data)
        response = self.user1.add_activity(activity_data)
        activities = self.user1.get(limit=2)['results']
        self.assertDatetimeAlmostEqual(activities[0]['time'], utcnow)
        self.assertClearlyNotEqual(activities[1]['time'], utcnow)

    def test_uniqueness_topic(self):
        '''
        In order for things to be considere unique they need:
        a.) The same time and activity data, or
        b.) The same time and foreign id
        '''
        # follow both the topic and the user
        self.flat3.follow('topic:1')
        self.flat3.follow('user:1')
        # add the same activity twice
        now = datetime.datetime.now(tzlocal())
        tweet = 'My Way %s' % random.randint(10, 100000)
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
        self.assertRaises(ValueError, lambda: self.c.feed('user1'))

    def test_serialization(self):
        today = datetime.date.today()
        now = datetime.datetime.now()
        data = dict(
            string='string', float=0.1, int=1, date=today, datetime=now)
        serialized = serializer.dumps(data)
        loaded = serializer.loads(serialized)
        self.assertEqual(data, loaded)

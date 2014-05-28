from unittest2.case import TestCase
import stream
import time
from stream.exceptions import ApiKeyException, InputException,\
    CustomFieldException
import random


def connect_debug():
    return stream.connect(
        u'5crf3bhfzesn',
        u'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
    )

client = connect_debug()
user1 = client.feed('user:1')
aggregated2 = client.feed('aggregated:2')
aggregated3 = client.feed('aggregated:3')
flat3 = client.feed('flat:3')


class ClientTest(TestCase):

    def setUp(self):
        # DEBUG account details
        self.c = client
        self.user1 = user1
        self.aggregated2 = aggregated2
        self.aggregated3 = aggregated3
        self.flat3 = flat3

    def test_add_activity(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        response = self.user1.add_activity(activity_data)
        activity_id = response['id']
        activities = self.user1.get(limit=1)['results']
        self.assertEqual(activities[0]['id'], activity_id)

    def test_remove_activity(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.user1.remove_activity(activity_id)
        activities = self.user1.get(limit=1)['results']
        self.assertNotEqual(activities[0]['id'], activity_id)

    def test_follow(self):
        actor_id = random.randint(10, 100000)
        activity_data = {'actor': actor_id, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.aggregated2.follow('user:1')
        time.sleep(5)
        activities = self.aggregated2.get(limit=3)['results']
        activity = self._get_first_aggregated_activity(activities)
        activity_id_found = activity['id'] if activity is not None else None
        self.assertEqual(activity_id_found, activity_id)

    def test_flat_follow(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.flat3.follow('user:1')
        time.sleep(5)
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

    def test_missing_field_exception(self):
        activity_data = {'actor': 1, 'verb': 'tweet',
                         'object': 1, 'debug_example_undefined': 'test'}
        self.assertRaises(CustomFieldException, lambda:
                          self.user1.add_activity(activity_data))

    def test_missing_actor(self):
        activity_data = {'verb': 'tweet', 'object':
                         1, 'debug_example_undefined': 'test'}
        self.assertRaises(InputException, lambda:
                          self.user1.add_activity(activity_data))

    def test_wrong_feed_spec(self):
        self.c = stream.connect(
            '5crf3bhfzesnMISSING',
            'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
        )
        self.assertRaises(ValueError, lambda: self.c.feed('user1'))

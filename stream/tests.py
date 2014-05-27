from unittest2.case import TestCase
import stream
import time


class ClientTest(TestCase):

    def setUp(self):
        # DEBUG account details
        self.c = stream.connect(
            '5crf3bhfzesn',
            'tfq2sdqpj9g446sbv653x3aqmgn33hsn8uzdc9jpskaw8mj6vsnhzswuwptuj9su'
        )
        self.user1 = self.c.feed('user:1')
        self.aggregated2 = self.c.feed('aggregated:2')
        self.flat3 = self.c.feed('flat:3')

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
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
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
        except IndexError, e:
            pass

    def _get_first_activity(self, activities):
        try:
            return activities[0]
        except IndexError, e:
            pass

    def test_unfollow(self):
        activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
        activity_id = self.user1.add_activity(activity_data)['id']
        self.aggregated2.follow('user:1')
        self.aggregated2.unfollow('user:1')
        time.sleep(5)
        activities = self.aggregated2.get(limit=3)['results']
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
        # try pk_lt based
        self.user1.get(limit=2, pk_lt=activity_id_two)['results']
        self.assertEqual(activities[0]['id'], activity_id)

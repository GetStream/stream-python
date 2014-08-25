from stream.utils import validate_feed


class Feed(object):

    def __init__(self, client, feed_id, token):
        '''
        Initializes the Feed class

        :param client: the api client
        :param feed_id: the feed id (string)


        '''
        self.client = client
        self.feed_id = feed_id
        self.feed_url = 'feed/%s/' % feed_id.replace(':', '/')
        self.feed_together = feed_id.replace(':', '')
        self.token = token
        self.authorization = self.feed_together + ' ' + self.token

    def add_to_signature(self, recipients):
        data = []
        for recipient in recipients:
            feed = self.client.feed(recipient)
            data.append("%s %s" % (recipient, feed.token))
        return data

    def add_activity(self, activity_data):
        '''
        Adds an activity to the feed, this will also trigger an update
        to all the feeds which follow this feed

        :param activity_data: a dict with the activity data

        **Example**::

            activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
            activity_id = feed.add_activity(activity_data)
        '''
        if activity_data.get('to'):
            activity_data['to'] = self.add_to_signature(activity_data['to'])

        result = self.client.post(
            self.feed_url, data=activity_data, authorization=self.authorization)
        return result

    def add_activities(self, activity_list):
        '''
        Adds a list of activities to the feed

        :param activity_list: a list with the activity data dicts

        **Example**::

            activity_data = [
                {'actor': 1, 'verb': 'tweet', 'object': 1},
                {'actor': 2, 'verb': 'watch', 'object': 2},
            ]
            result = feed.add_activities(activity_data)
        '''
        for activity_data in activity_list:
            if activity_data.get('to'):
                activity_data['to'] = self.add_to_signature(
                    activity_data['to'])

        data = dict(activities=activity_list)
        result = self.client.post(
            self.feed_url, data=data, authorization=self.authorization)
        return result

    def remove_activity(self, activity_id=None, foreign_id=None):
        '''
        Removes an activity from the feed

        :param activity_id: the activity id to remove from this feed
        (note this will also remove the activity from feeds which follow this feed)
        :param foreign_id: the foreign id you provided when adding the activity
        '''
        identifier = activity_id or foreign_id
        if not identifier:
            raise ValueError('please either provide activity_id or foreign_id')
        url = self.feed_url + '%s/' % identifier
        params = dict()
        if foreign_id is not None:
            params['foreign_id'] = '1'
        result = self.client.delete(
            url, authorization=self.authorization, params=params)
        return result

    def follow(self, target_feed):
        '''
        Follows the given feed

        :param target_feed: the feed to follow, ie flat:3
        '''
        url = self.feed_url + 'follows/'
        data = {
            'target': target_feed,
            'target_token': self.client.feed(target_feed).token
        }
        response = self.client.post(
            url, data=data, authorization=self.authorization)
        return response

    def followers(self, offset=0, limit=25):
        params = {
            'limit': limit,
            'offset': offset
        }
        url = self.feed_url + 'followers/'
        response = self.client.get(
            url, params=params, authorization=self.authorization)
        return response

    def following(self, offset=0, limit=25, feeds=None):
        feeds = feeds is not None and ','.join(feeds) or ''
        params = {
            'offset': offset,
            'limit': limit,
            'filter': feeds
        }
        url = self.feed_url + 'follows/'
        response = self.client.get(
            url, params=params, authorization=self.authorization)
        return response

    def unfollow(self, target_feed):
        '''
        Unfollow the given feed
        '''
        validate_feed(target_feed)
        url = self.feed_url + 'follows/%s/' % target_feed
        response = self.client.delete(url, authorization=self.authorization)
        return response

    def get(self, **params):
        '''
        Get the activities in this feed

        **Example**::

            # fast pagination using id filtering
            feed.get(limit=10, id_lte=100292310)

            # slow pagination using offset
            feed.get(limit=10, offset=10)
        '''
        response = self.client.get(
            self.feed_url, params=params, authorization=self.authorization)
        return response

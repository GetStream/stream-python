from stream.utils import validate_feed_id, validate_user_id, validate_feed_slug


class Feed(object):

    def __init__(self, client, feed_slug, user_id, token):
        '''
        Initializes the Feed class

        :param client: the api client
        :param slug: the slug of the feed, ie user, flat, notification
        :param user_id: the id of the user
        :param token: the token
        '''
        self.client = client
        self.slug = feed_slug
        self.user_id = str(user_id)
        self.id = '%s:%s' % (feed_slug, user_id)
        self.token = token

        self.feed_url = 'feed/%s/' % self.id.replace(':', '/')
        self.feed_together = self.id.replace(':', '')
        self.signature = self.feed_together + ' ' + self.token

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
            self.feed_url, data=activity_data, signature=self.signature)
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
            self.feed_url, data=data, signature=self.signature)
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
            url, signature=self.signature, params=params)
        return result

    def get(self, **params):
        '''
        Get the activities in this feed

        **Example**::

            # fast pagination using id filtering
            feed.get(limit=10, id_lte=100292310)

            # slow pagination using offset
            feed.get(limit=10, offset=10)
        '''
        mark_read = params.get('mark_read')
        if isinstance(mark_read, (list, tuple)):
            params['mark_read'] = ','.join(mark_read)
        response = self.client.get(
            self.feed_url, params=params, signature=self.signature)
        return response

    def follow(self, target_feed_slug, target_user_id):
        '''
        Follows the given feed

        :param target_feed_slug: the slug of the target feed
        :param target_user_id: the user id
        '''
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = '%s:%s' % (target_feed_slug, target_user_id)
        url = self.feed_url + 'follows/'
        data = {
            'target': target_feed_id,
            'target_token': self.client.feed(target_feed_slug, target_user_id).token
        }
        response = self.client.post(
            url, data=data, signature=self.signature)
        return response

    def unfollow(self, target_feed_slug, target_user_id):
        '''
        Unfollow the given feed
        '''
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = '%s:%s' % (target_feed_slug, target_user_id)
        url = self.feed_url + 'follows/%s/' % target_feed_id
        response = self.client.delete(url, signature=self.signature)
        return response

    def followers(self, offset=0, limit=25, feeds=None):
        '''
        Lists the followers for the given feed
        '''
        feeds = feeds is not None and ','.join(feeds) or ''
        params = {
            'limit': limit,
            'offset': offset,
            'filter': feeds
        }
        url = self.feed_url + 'followers/'
        response = self.client.get(
            url, params=params, signature=self.signature)
        return response

    def following(self, offset=0, limit=25, feeds=None):
        '''
        List the feeds which this feed is following
        '''
        feeds = feeds is not None and ','.join(feeds) or ''
        params = {
            'offset': offset,
            'limit': limit,
            'filter': feeds
        }
        url = self.feed_url + 'follows/'
        response = self.client.get(
            url, params=params, signature=self.signature)
        return response

    def add_to_signature(self, recipients):
        '''
        Takes a list of recipients such as ['user:1', 'user:2']
        and turns it into a list with the tokens included
        ['user:1 token', 'user:2 token']
        '''
        data = []
        for recipient in recipients:
            validate_feed_id(recipient)
            feed_slug, user_id = recipient.split(':')
            feed = self.client.feed(feed_slug, user_id)
            data.append("%s %s" % (recipient, feed.token))
        return data

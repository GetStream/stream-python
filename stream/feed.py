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
        self.feed_targets_url = 'feed_targets/%s/' % self.id.replace(':', '/')
        self.feed_together = self.id.replace(':', '')
        self.signature = self.feed_together + ' ' + self.token

    def create_scope_token(self, resource, action):
        '''
        creates the JWT token to perform an action on a owned resource
        '''
        return self.client.create_jwt_token(resource, action, feed_id=self.feed_together)

    def get_readonly_token(self):
        '''
        creates the JWT token to perform readonly operations
        '''
        return self.create_scope_token('*', 'read')

    def add_activity(self, activity_data):
        '''
        Adds an activity to the feed, this will also trigger an update
        to all the feeds which follow this feed

        :param activity_data: a dict with the activity data

        **Example**::

            activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
            activity_id = feed.add_activity(activity_data)
        '''
        if activity_data.get('to') and not isinstance(activity_data.get('to'), (list, tuple, set)):
            raise TypeError('please provide the activity\'s to field as a list not a string')

        if activity_data.get('to'):
            activity_data = activity_data.copy()
            activity_data['to'] = self.add_to_signature(activity_data['to'])

        token = self.create_scope_token('feed', 'write')
        result = self.client.post(
            self.feed_url, data=activity_data, signature=token)
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
        activities = []
        for activity_data in activity_list:
            activity_data = activity_data.copy()
            activities.append(activity_data)
            if activity_data.get('to'):
                activity_data['to'] = self.add_to_signature(
                    activity_data['to'])
        token = self.create_scope_token('feed', 'write')
        data = dict(activities=activities)
        if activities:
            result = self.client.post(
                self.feed_url, data=data, signature=token)
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
        token = self.create_scope_token('feed', 'delete')
        if foreign_id is not None:
            params['foreign_id'] = '1'
        result = self.client.delete(
            url, signature=token, params=params)
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
        for field in ['mark_read', 'mark_seen']:
            value = params.get(field)
            if isinstance(value, (list, tuple)):
                params[field] = ','.join(value)
        token = self.create_scope_token('feed', 'read')
        response = self.client.get(
            self.feed_url, params=params, signature=token)
        return response

    def follow(self, target_feed_slug, target_user_id, activity_copy_limit=None, **extra_data):
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
        if activity_copy_limit != None:
            data['activity_copy_limit'] = activity_copy_limit
        token = self.create_scope_token('follower', 'write')
        data.update(extra_data)
        response = self.client.post(
            url, data=data, signature=token)
        return response

    def unfollow(self, target_feed_slug, target_user_id, keep_history=False):
        '''
        Unfollow the given feed
        '''
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = '%s:%s' % (target_feed_slug, target_user_id)
        token = self.create_scope_token('follower', 'delete')
        url = self.feed_url + 'follows/%s/' % target_feed_id
        params = {}
        if keep_history:
            params['keep_history'] = True
        response = self.client.delete(url, signature=token, params=params)
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
        token = self.create_scope_token('follower', 'read')
        response = self.client.get(
            url, params=params, signature=token)
        return response

    def following(self, offset=0, limit=25, feeds=None, filter=None):
        '''
        List the feeds which this feed is following
        '''
        if feeds is not None:
            feeds = feeds is not None and ','.join(feeds) or ''
        params = {
            'offset': offset,
            'limit': limit,
            'filter': feeds
        }
        url = self.feed_url + 'follows/'
        token = self.create_scope_token('follower', 'read')
        response = self.client.get(
            url, params=params, signature=token)
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

    def update_activity_to_targets(self, foreign_id, time,
                                   new_targets=None, added_targets=None,
                                   removed_targets=None):
        data = {
            'foreign_id': foreign_id,
            'time': time,
        }

        if new_targets is not None:
            data['new_targets'] = new_targets
        if added_targets is not None:
            data['added_targets'] = added_targets
        if removed_targets is not None:
            data['removed_targets'] = removed_targets

        url = self.feed_targets_url + 'activity_to_targets/'

        token = self.create_scope_token('feed_targets', 'write')
        return self.client.post(url, data=data, signature=token)

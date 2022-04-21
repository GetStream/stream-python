from abc import ABC, abstractmethod

from stream.utils import validate_feed_id


class AbstractFeed(ABC):
    @abstractmethod
    def create_scope_token(self, resource, action):
        """
        creates the JWT token to perform an action on a owned resource
        """
        pass

    @abstractmethod
    def get_readonly_token(self):
        """
        creates the JWT token to perform readonly operations
        """
        pass

    @abstractmethod
    def add_activity(self, activity_data):
        """
        Adds an activity to the feed, this will also trigger an update
        to all the feeds which follow this feed

        :param activity_data: a dict with the activity data

        **Example**::

            activity_data = {'actor': 1, 'verb': 'tweet', 'object': 1}
            activity_id = feed.add_activity(activity_data)
        """
        pass

    @abstractmethod
    def add_activities(self, activity_list):
        """
        Adds a list of activities to the feed

        :param activity_list: a list with the activity data dicts

        **Example**::

            activity_data = [
                {'actor': 1, 'verb': 'tweet', 'object': 1},
                {'actor': 2, 'verb': 'watch', 'object': 2},
            ]
            result = feed.add_activities(activity_data)
        """
        pass

    @abstractmethod
    def remove_activity(self, activity_id=None, foreign_id=None):
        """
        Removes an activity from the feed

        :param activity_id: the activity id to remove from this feed
        (note this will also remove the activity from feeds which follow this feed)
        :param foreign_id: the foreign id you provided when adding the activity
        """
        pass

    @abstractmethod
    def get(self, enrich=False, reactions=None, **params):
        """
        Get the activities in this feed

        **Example**::

            # fast pagination using id filtering
            feed.get(limit=10, id_lte=100292310)

            # slow pagination using offset
            feed.get(limit=10, offset=10)
        """
        pass

    @abstractmethod
    def follow(
        self, target_feed_slug, target_user_id, activity_copy_limit=None, **extra_data
    ):
        """
        Follows the given feed

        :param activity_copy_limit: how many activities should be copied from target
         feed
        :param target_feed_slug: the slug of the target feed
        :param target_user_id: the user id
        """
        pass

    @abstractmethod
    def unfollow(self, target_feed_slug, target_user_id, keep_history=False):
        """
        Unfollow the given feed
        """
        pass

    @abstractmethod
    def followers(self, offset=0, limit=25, feeds=None):
        """
        Lists the followers for the given feed
        """
        pass

    @abstractmethod
    def following(self, offset=0, limit=25, feeds=None):
        """
        List the feeds which this feed is following
        """
        pass

    @abstractmethod
    def add_to_signature(self, recipients):
        """
        Takes a list of recipients such as ['user:1', 'user:2']
        and turns it into a list with the tokens included
        ['user:1 token', 'user:2 token']
        """
        pass

    @abstractmethod
    def update_activity_to_targets(
        self,
        foreign_id,
        time,
        new_targets=None,
        added_targets=None,
        removed_targets=None,
    ):
        pass


class BaseFeed(AbstractFeed, ABC):
    def __init__(self, client, feed_slug, user_id, token):
        """
        Initializes the Feed class

        :param client: the api client
        :param feed_slug: the slug of the feed, ie user, flat, notification
        :param user_id: the id of the user
        :param token: the token
        """
        self.client = client
        self.slug = feed_slug
        self.user_id = f"{user_id}"
        self.id = f"{feed_slug}:{user_id}"
        self.token = token.decode("utf-8") if isinstance(token, bytes) else token
        _id = self.id.replace(":", "/")
        self.feed_url = f"feed/{_id}/"
        self.enriched_feed_url = f"enrich/feed/{_id}/"
        self.feed_targets_url = f"feed_targets/{_id}/"
        self.feed_together = self.id.replace(":", "")
        self.signature = f"{self.feed_together} {self.token}"

    def create_scope_token(self, resource, action):
        return self.client.create_jwt_token(
            resource, action, feed_id=self.feed_together
        )

    def get_readonly_token(self):
        return self.create_scope_token("*", "read")

    def add_to_signature(self, recipients):
        data = []
        for recipient in recipients:
            validate_feed_id(recipient)
            feed_slug, user_id = recipient.split(":")
            feed = self.client.feed(feed_slug, user_id)
            data.append(f"{recipient} {feed.token}")
        return data

from stream.feed.base import BaseFeed
from stream.utils import get_reaction_params, validate_feed_slug, validate_user_id


class Feed(BaseFeed):
    def add_activity(self, activity_data):
        if activity_data.get("to") and not isinstance(
            activity_data.get("to"), (list, tuple, set)
        ):
            raise TypeError(
                "please provide the activity's to field as a list not a string"
            )

        if activity_data.get("to"):
            activity_data = activity_data.copy()
            activity_data["to"] = self.add_to_signature(activity_data["to"])

        token = self.create_scope_token("feed", "write")
        return self.client.post(self.feed_url, data=activity_data, signature=token)

    def add_activities(self, activity_list):
        activities = []
        for activity_data in activity_list:
            activity_data = activity_data.copy()
            activities.append(activity_data)
            if activity_data.get("to"):
                activity_data["to"] = self.add_to_signature(activity_data["to"])
        token = self.create_scope_token("feed", "write")
        data = dict(activities=activities)
        if activities:
            return self.client.post(self.feed_url, data=data, signature=token)
        return None

    def remove_activity(self, activity_id=None, foreign_id=None):
        identifier = activity_id or foreign_id
        if not identifier:
            raise ValueError("please either provide activity_id or foreign_id")
        url = f"{self.feed_url}{identifier}/"
        params = dict()
        token = self.create_scope_token("feed", "delete")
        if foreign_id is not None:
            params["foreign_id"] = "1"
        return self.client.delete(url, signature=token, params=params)

    def get(self, enrich=False, reactions=None, **params):
        for field in ["mark_read", "mark_seen"]:
            value = params.get(field)
            if isinstance(value, (list, tuple)):
                params[field] = ",".join(value)
        token = self.create_scope_token("feed", "read")

        if enrich or reactions is not None:
            feed_url = self.enriched_feed_url
        else:
            feed_url = self.feed_url

        params.update(get_reaction_params(reactions))
        return self.client.get(feed_url, params=params, signature=token)

    def follow(
        self, target_feed_slug, target_user_id, activity_copy_limit=None, **extra_data
    ):
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = f"{target_feed_slug}:{target_user_id}"
        url = f"{self.feed_url}follows/"
        target_token = self.client.feed(target_feed_slug, target_user_id).token
        data = {"target": target_feed_id, "target_token": target_token}
        if activity_copy_limit is not None:
            data["activity_copy_limit"] = activity_copy_limit
        token = self.create_scope_token("follower", "write")
        data.update(extra_data)
        return self.client.post(url, data=data, signature=token)

    def unfollow(self, target_feed_slug, target_user_id, keep_history=False):
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = f"{target_feed_slug}:{target_user_id}"
        token = self.create_scope_token("follower", "delete")
        url = f"{self.feed_url}follows/{target_feed_id}/"
        params = {}
        if keep_history:
            params["keep_history"] = True
        return self.client.delete(url, signature=token, params=params)

    def followers(self, offset=0, limit=25, feeds=None):
        feeds = ",".join(feeds) if feeds is not None else ""
        params = {"limit": limit, "offset": offset, "filter": feeds}
        url = f"{self.feed_url}followers/"
        token = self.create_scope_token("follower", "read")
        return self.client.get(url, params=params, signature=token)

    def following(self, offset=0, limit=25, feeds=None):
        feeds = ",".join(feeds) if feeds is not None else ""
        params = {"offset": offset, "limit": limit, "filter": feeds}
        url = f"{self.feed_url}follows/"
        token = self.create_scope_token("follower", "read")
        return self.client.get(url, params=params, signature=token)

    def update_activity_to_targets(
        self,
        foreign_id,
        time,
        new_targets=None,
        added_targets=None,
        removed_targets=None,
    ):
        data = {"foreign_id": foreign_id, "time": time}

        if new_targets is not None:
            data["new_targets"] = new_targets
        if added_targets is not None:
            data["added_targets"] = added_targets
        if removed_targets is not None:
            data["removed_targets"] = removed_targets

        url = f"{self.feed_targets_url}activity_to_targets/"
        token = self.create_scope_token("feed_targets", "write")
        return self.client.post(url, data=data, signature=token)


class AsyncFeed(BaseFeed):
    async def add_activity(self, activity_data):
        if activity_data.get("to") and not isinstance(
            activity_data.get("to"), (list, tuple, set)
        ):
            raise TypeError(
                "please provide the activity's to field as a list not a string"
            )

        if activity_data.get("to"):
            activity_data = activity_data.copy()
            activity_data["to"] = self.add_to_signature(activity_data["to"])

        token = self.create_scope_token("feed", "write")
        return await self.client.post(
            self.feed_url, data=activity_data, signature=token
        )

    async def add_activities(self, activity_list):
        activities = []
        for activity_data in activity_list:
            activity_data = activity_data.copy()
            activities.append(activity_data)
            if activity_data.get("to"):
                activity_data["to"] = self.add_to_signature(activity_data["to"])
        token = self.create_scope_token("feed", "write")
        data = dict(activities=activities)
        if not activities:
            return

        return await self.client.post(self.feed_url, data=data, signature=token)

    async def remove_activity(self, activity_id=None, foreign_id=None):
        identifier = activity_id or foreign_id
        if not identifier:
            raise ValueError("please either provide activity_id or foreign_id")
        url = f"{self.feed_url}{identifier}/"
        params = dict()
        token = self.create_scope_token("feed", "delete")
        if foreign_id is not None:
            params["foreign_id"] = "1"
        return await self.client.delete(url, signature=token, params=params)

    async def get(self, enrich=False, reactions=None, **params):
        for field in ["mark_read", "mark_seen"]:
            value = params.get(field)
            if isinstance(value, (list, tuple)):
                params[field] = ",".join(value)

        token = self.create_scope_token("feed", "read")
        if enrich or reactions is not None:
            feed_url = self.enriched_feed_url
        else:
            feed_url = self.feed_url

        params.update(get_reaction_params(reactions))
        return await self.client.get(feed_url, params=params, signature=token)

    async def follow(
        self, target_feed_slug, target_user_id, activity_copy_limit=None, **extra_data
    ):
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = f"{target_feed_slug}:{target_user_id}"
        url = f"{self.feed_url}follows/"
        target_token = self.client.feed(target_feed_slug, target_user_id).token
        data = {"target": target_feed_id, "target_token": target_token}
        if activity_copy_limit is not None:
            data["activity_copy_limit"] = activity_copy_limit
        token = self.create_scope_token("follower", "write")
        data.update(extra_data)
        return await self.client.post(url, data=data, signature=token)

    async def unfollow(self, target_feed_slug, target_user_id, keep_history=False):
        target_feed_slug = validate_feed_slug(target_feed_slug)
        target_user_id = validate_user_id(target_user_id)
        target_feed_id = f"{target_feed_slug}:{target_user_id}"
        token = self.create_scope_token("follower", "delete")
        url = f"{self.feed_url}follows/{target_feed_id}/"
        params = {}
        if keep_history:
            params["keep_history"] = True
        return await self.client.delete(url, signature=token, params=params)

    async def followers(self, offset=0, limit=25, feeds=None):
        feeds = ",".join(feeds) if feeds is not None else ""
        params = {"limit": limit, "offset": offset, "filter": feeds}
        url = f"{self.feed_url}followers/"
        token = self.create_scope_token("follower", "read")
        return await self.client.get(url, params=params, signature=token)

    async def following(self, offset=0, limit=25, feeds=None):
        feeds = ",".join(feeds) if feeds is not None else ""
        params = {"offset": offset, "limit": limit, "filter": feeds}
        url = f"{self.feed_url}follows/"
        token = self.create_scope_token("follower", "read")
        return await self.client.get(url, params=params, signature=token)

    async def update_activity_to_targets(
        self,
        foreign_id,
        time,
        new_targets=None,
        added_targets=None,
        removed_targets=None,
    ):
        data = {"foreign_id": foreign_id, "time": time}
        if new_targets is not None:
            data["new_targets"] = new_targets
        if added_targets is not None:
            data["added_targets"] = added_targets
        if removed_targets is not None:
            data["removed_targets"] = removed_targets

        url = f"{self.feed_targets_url}activity_to_targets/"
        token = self.create_scope_token("feed_targets", "write")
        return await self.client.post(url, data=data, signature=token)

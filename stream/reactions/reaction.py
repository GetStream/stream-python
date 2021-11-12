from stream.reactions.base import BaseReactions


class Reactions(BaseReactions):
    def add(
        self,
        kind,
        activity_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        payload = dict(
            kind=kind,
            activity_id=activity_id,
            data=data,
            target_feeds=target_feeds,
            target_feeds_extra_data=target_feeds_extra_data,
            user_id=user_id,
        )
        return self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def get(self, reaction_id):
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return self.client.get(
            url, service_name=self.SERVICE_NAME, signature=self.token
        )

    def update(self, reaction_id, data=None, target_feeds=None):
        payload = dict(data=data, target_feeds=target_feeds)
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return self.client.put(
            url,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def delete(self, reaction_id):
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return self.client.delete(
            url, service_name=self.SERVICE_NAME, signature=self.token
        )

    def add_child(
        self,
        kind,
        parent_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        payload = dict(
            kind=kind,
            parent=parent_id,
            data=data,
            target_feeds=target_feeds,
            target_feeds_extra_data=target_feeds_extra_data,
            user_id=user_id,
        )
        return self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def filter(self, **params):
        endpoint = self._prepare_endpoint_for_filter(**params)
        return self.client.get(
            endpoint,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            params=params,
        )


class AsyncReactions(BaseReactions):
    async def add(
        self,
        kind,
        activity_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        payload = dict(
            kind=kind,
            activity_id=activity_id,
            data=data,
            target_feeds=target_feeds,
            target_feeds_extra_data=target_feeds_extra_data,
            user_id=user_id,
        )
        return await self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def get(self, reaction_id):
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return await self.client.get(
            url, service_name=self.SERVICE_NAME, signature=self.token
        )

    async def update(self, reaction_id, data=None, target_feeds=None):
        payload = dict(data=data, target_feeds=target_feeds)
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return await self.client.put(
            url,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def delete(self, reaction_id):
        url = f"{self.API_ENDPOINT}{reaction_id}"
        return await self.client.delete(
            url, service_name=self.SERVICE_NAME, signature=self.token
        )

    async def add_child(
        self,
        kind,
        parent_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        payload = dict(
            kind=kind,
            parent=parent_id,
            data=data,
            target_feeds=target_feeds,
            target_feeds_extra_data=target_feeds_extra_data,
            user_id=user_id,
        )
        return await self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def filter(self, **params):
        endpoint = self._prepare_endpoint_for_filter(**params)
        return await self.client.get(
            endpoint,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            params=params,
        )

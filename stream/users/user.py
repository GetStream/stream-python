from stream.users.base import BaseUsers


class Users(BaseUsers):
    def add(self, user_id, data=None, get_or_create=False):
        payload = dict(id=user_id, data=data)
        return self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
            params={"get_or_create": get_or_create},
        )

    def get(self, user_id, **params):
        return self.client.get(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    def update(self, user_id, data=None):
        payload = dict(data=data)
        return self.client.put(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def delete(self, user_id):
        return self.client.delete(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )


class AsyncUsers(BaseUsers):
    async def add(self, user_id, data=None, get_or_create=False):
        payload = dict(id=user_id, data=data)
        return await self.client.post(
            self.API_ENDPOINT,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
            params={"get_or_create": str(get_or_create)},
        )

    async def get(self, user_id, **params):
        return await self.client.get(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    async def update(self, user_id, data=None):
        payload = dict(data=data)
        return await self.client.put(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def delete(self, user_id):
        return await self.client.delete(
            f"{self.API_ENDPOINT}/{user_id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )

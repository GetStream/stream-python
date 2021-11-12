from stream.collections.base import BaseCollection


class Collections(BaseCollection):
    def upsert(self, collection_name, data):
        if not isinstance(data, list):
            data = [data]

        data_json = {collection_name: data}

        return self.client.post(
            self.URL,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data={"data": data_json},
        )

    def select(self, collection_name, ids):
        if not isinstance(ids, list):
            ids = [ids]

        foreign_ids = ",".join(
            f"{collection_name}:{k}" for i, k in enumerate(ids)
        )

        return self.client.get(
            self.URL,
            service_name=self.SERVICE_NAME,
            params={"foreign_ids": foreign_ids},
            signature=self.token,
        )

    def delete_many(self, collection_name, ids):
        if not isinstance(ids, list):
            ids = [ids]
        ids = [str(i) for i in ids]

        params = {"collection_name": collection_name, "ids": ids}

        return self.client.delete(
            self.URL,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    def add(self, collection_name, data, id=None, user_id=None):
        payload = dict(id=id, data=data, user_id=user_id)
        return self.client.post(
            f"{self.URL}/{collection_name}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def get(self, collection_name, id):
        return self.client.get(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )

    def update(self, collection_name, id, data=None):
        payload = dict(data=data)
        return self.client.put(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    def delete(self, collection_name, id):
        return self.client.delete(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )


class AsyncCollections(BaseCollection):
    async def upsert(self, collection_name, data):
        if not isinstance(data, list):
            data = [data]

        data_json = {collection_name: data}

        return await self.client.post(
            self.URL,
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data={"data": data_json},
        )

    async def select(self, collection_name, ids):
        if not isinstance(ids, list):
            ids = [ids]

        foreign_ids = ",".join(f"{collection_name}:{k}" for i, k in enumerate(ids))

        return await self.client.get(
            self.URL,
            service_name=self.SERVICE_NAME,
            params={"foreign_ids": foreign_ids},
            signature=self.token,
        )

    async def delete_many(self, collection_name, ids):
        if not isinstance(ids, list):
            ids = [ids]
        ids = [str(i) for i in ids]

        params = {"collection_name": collection_name, "ids": ids}
        return await self.client.delete(
            self.URL,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    async def get(self, collection_name, id):
        return await self.client.get(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )

    async def add(self, collection_name, data, id=None, user_id=None):
        payload = dict(id=id, data=data, user_id=user_id)
        return await self.client.post(
            f"{self.URL}/{collection_name}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def update(self, collection_name, id, data=None):
        payload = dict(data=data)
        return await self.client.put(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
            data=payload,
        )

    async def delete(self, collection_name, id):
        return await self.client.delete(
            f"{self.URL}/{collection_name}/{id}",
            service_name=self.SERVICE_NAME,
            signature=self.token,
        )

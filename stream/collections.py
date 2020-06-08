class Collections:
    def __init__(self, client, token):
        """
        Used to manipulate data at the 'meta' endpoint
        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

    def create_reference(self, collection_name=None, id=None, entry=None):
        if isinstance(entry, (dict,)):
            _collection = entry["collection"]
            _id = entry["id"]
        elif collection_name is not None and id is not None:
            _collection = collection_name
            _id = id
        else:
            raise ValueError(
                "must call with collection_name and id or with entry arguments"
            )
        return "SO:%s:%s" % (_collection, _id)

    def upsert(self, collection_name, data):
        """
        "Insert new or update existing data.
        :param collection_name: Collection Name i.e 'user'
        :param data: list of dictionaries
        :return: http response, 201 if successful along with data posted.

        **Example**::
            client.collections.upsert('user', [{"id": '1', "name": "Juniper", "hobbies": ["Playing", "Sleeping", "Eating"]},
                                           {"id": '2', "name": "Ruby", "interests": ["Sunbeams", "Surprise Attacks"]}])
        """

        if not isinstance(data, list):
            data = [data]

        data_json = {collection_name: data}

        return self.client.post(
            "collections/",
            service_name="api",
            signature=self.token,
            data={"data": data_json},
        )

    def select(self, collection_name, ids):
        """
        Retrieve data from meta endpoint, can include data you've uploaded or personalization/analytic data
        created by the stream team.
        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids of feed group i.e [123,456]
        :return: meta data as json blob

        **Example**::
            client.collections.select('user', 1)
            client.collections.select('user', [1,2,3])
        """

        if not isinstance(ids, list):
            ids = [ids]

        foreign_ids = ",".join(
            "%s:%s" % (collection_name, k) for i, k in enumerate(ids)
        )

        return self.client.get(
            "collections/",
            service_name="api",
            params={"foreign_ids": foreign_ids},
            signature=self.token,
        )

    def delete_many(self, collection_name, ids):
        """
        Delete data from meta.
        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids to delete i.e [123,456]
        :return: data that was deleted if successful or not.

        **Example**::
            client.collections.delete('user', '1')
            client.collections.delete('user', ['1','2','3'])
        """

        if not isinstance(ids, list):
            ids = [ids]
        ids = [str(i) for i in ids]

        params = {"collection_name": collection_name, "ids": ids}

        return self.client.delete(
            "collections/", service_name="api", params=params, signature=self.token
        )

    def add(self, collection_name, data, id=None, user_id=None):
        payload = dict(id=id, data=data, user_id=user_id)
        return self.client.post(
            "collections/%s" % collection_name,
            service_name="api",
            signature=self.token,
            data=payload,
        )

    def get(self, collection_name, id):
        return self.client.get(
            "collections/%s/%s" % (collection_name, id),
            service_name="api",
            signature=self.token,
        )

    def update(self, collection_name, id, data=None):
        payload = dict(data=data)
        return self.client.put(
            "collections/%s/%s" % (collection_name, id),
            service_name="api",
            signature=self.token,
            data=payload,
        )

    def delete(self, collection_name, id):
        return self.client.delete(
            "collections/%s/%s" % (collection_name, id),
            service_name="api",
            signature=self.token,
        )

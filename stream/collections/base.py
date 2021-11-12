from abc import ABC, abstractmethod


class AbstractCollection(ABC):
    @abstractmethod
    def create_reference(self, collection_name=None, id=None, entry=None):
        pass

    @abstractmethod
    def upsert(self, collection_name, data):
        """
        "Insert new or update existing data.
        :param collection_name: Collection Name i.e 'user'
        :param data: list of dictionaries
        :return: http response, 201 if successful along with data posted.

        **Example**::
            client.collections.upsert(
            'user', [
                {"id": '1', "name": "Juniper", "hobbies": ["Playing", "Sleeping", "Eating"]},
                {"id": '2', "name": "Ruby", "interests": ["Sunbeams", "Surprise Attacks"]}
            ]
            )
        """
        pass

    @abstractmethod
    def select(self, collection_name, ids):
        """
        Retrieve data from meta endpoint, can include data you've uploaded or
        personalization/analytic data
        created by the stream team.
        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids of feed group i.e [123,456]
        :return: meta data as json blob

        **Example**::
            client.collections.select('user', 1)
            client.collections.select('user', [1,2,3])
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def add(self, collection_name, data, id=None, user_id=None):
        pass

    @abstractmethod
    def get(self, collection_name, id):
        pass

    @abstractmethod
    def update(self, collection_name, id, data=None):
        pass

    @abstractmethod
    def delete(self, collection_name, id):
        pass


class BaseCollection(AbstractCollection, ABC):

    URL = "collections/"
    SERVICE_NAME = "api"

    def __init__(self, client, token):
        """
        Used to manipulate data at the 'meta' endpoint
        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

    def create_reference(self, collection_name=None, id=None, entry=None):
        if isinstance(entry, dict):
            _collection = entry["collection"]
            _id = entry["id"]
        elif collection_name is not None and id is not None:
            _collection = collection_name
            _id = id
        else:
            raise ValueError(
                "must call with collection_name and id or with entry arguments"
            )
        return f"SO:{_collection}:{_id}"

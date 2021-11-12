from abc import ABC, abstractmethod


class AbstractUsers(ABC):
    @abstractmethod
    def create_reference(self, id):
        pass

    @abstractmethod
    def add(self, user_id, data=None, get_or_create=False):
        pass

    @abstractmethod
    def get(self, user_id, **params):
        pass

    @abstractmethod
    def update(self, user_id, data=None):
        pass

    @abstractmethod
    def delete(self, user_id):
        pass


class BaseUsers(AbstractUsers, ABC):

    API_ENDPOINT = "user/"
    SERVICE_NAME = "api"

    def __init__(self, client, token):
        self.client = client
        self.token = token

    def create_reference(self, id):
        _id = id
        if isinstance(id, (dict,)) and id.get("id") is not None:
            _id = id.get("id")
        return f"SU:{_id}"

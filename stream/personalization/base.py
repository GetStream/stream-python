from abc import ABC, abstractmethod


class AbstractPersonalization(ABC):
    @abstractmethod
    def get(self, resource, **params):
        pass

    @abstractmethod
    def post(self, resource, **params):
        pass

    @abstractmethod
    def delete(self, resource, **params):
        pass


class BasePersonalization(AbstractPersonalization, ABC):

    SERVICE_NAME = "personalization"

    def __init__(self, client, token):
        """
        Methods to interact with personalized feeds.
        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

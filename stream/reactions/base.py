from abc import ABC, abstractmethod


class AbstractReactions(ABC):
    @abstractmethod
    def add(
        self,
        kind,
        activity_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        pass

    @abstractmethod
    def get(self, reaction_id):
        pass

    @abstractmethod
    def update(self, reaction_id, data=None, target_feeds=None):
        pass

    @abstractmethod
    def delete(self, reaction_id):
        pass

    @abstractmethod
    def add_child(
        self,
        kind,
        parent_id,
        user_id,
        data=None,
        target_feeds=None,
        target_feeds_extra_data=None,
    ):
        pass

    @abstractmethod
    def filter(self, **params):
        pass


class BaseReactions(AbstractReactions, ABC):

    API_ENDPOINT = "reaction/"
    SERVICE_NAME = "api"

    def __init__(self, client, token):
        self.client = client
        self.token = token

    def _prepare_endpoint_for_filter(self, **params):
        lookup_field = ""
        lookup_value = ""

        kind = params.pop("kind", None)

        if params.get("reaction_id"):
            lookup_field = "reaction_id"
            lookup_value = params.pop("reaction_id")
        elif params.get("activity_id"):
            lookup_field = "activity_id"
            lookup_value = params.pop("activity_id")
        elif params.get("user_id"):
            lookup_field = "user_id"
            lookup_value = params.pop("user_id")

        endpoint = f"{self.API_ENDPOINT}{lookup_field}/{lookup_value}/"
        if kind is not None:
            endpoint += f"{kind}/"

        return endpoint

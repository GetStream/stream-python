class Reactions:
    def __init__(self, client, token):
        self.client = client
        self.token = token

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
            "reaction/", service_name="api", signature=self.token, data=payload
        )

    def get(self, reaction_id):
        return self.client.get(
            "reaction/%s" % reaction_id, service_name="api", signature=self.token
        )

    def update(self, reaction_id, data=None, target_feeds=None):
        payload = dict(data=data, target_feeds=target_feeds)
        return self.client.put(
            "reaction/%s" % reaction_id,
            service_name="api",
            signature=self.token,
            data=payload,
        )

    def delete(self, reaction_id):
        return self.client.delete(
            "reaction/%s" % reaction_id, service_name="api", signature=self.token
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
            "reaction/", service_name="api", signature=self.token, data=payload
        )

    def filter(self, **params):
        lookup_field = ""
        lookup_value = ""

        kind = params.pop("kind", None)

        if "reaction_id" in params:
            lookup_field = "reaction_id"
            lookup_value = params.pop("reaction_id")
        elif "activity_id" in params:
            lookup_field = "activity_id"
            lookup_value = params.pop("activity_id")
        elif "user_id" in params:
            lookup_field = "user_id"
            lookup_value = params.pop("user_id")

        endpoint = "reaction/%s/%s/" % (lookup_field, lookup_value)
        if kind is not None:
            endpoint = "reaction/%s/%s/%s/" % (lookup_field, lookup_value, kind)

        return self.client.get(
            endpoint, service_name="api", signature=self.token, params=params
        )

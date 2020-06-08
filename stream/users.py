class Users:
    def __init__(self, client, token):
        self.client = client
        self.token = token

    def create_reference(self, id):
        _id = id
        if isinstance(id, (dict,)) and id.get("id") is not None:
            _id = id.get("id")
        return "SU:%s" % _id

    def add(self, user_id, data=None, get_or_create=False):
        payload = dict(id=user_id, data=data)
        return self.client.post(
            "user/",
            service_name="api",
            signature=self.token,
            data=payload,
            params={"get_or_create": get_or_create},
        )

    def get(self, user_id, **params):
        return self.client.get(
            "user/%s" % user_id, service_name="api", params=params, signature=self.token
        )

    def update(self, user_id, data=None):
        payload = dict(data=data)
        return self.client.put(
            "user/%s" % user_id, service_name="api", signature=self.token, data=payload
        )

    def delete(self, user_id):
        return self.client.delete(
            "user/%s" % user_id, service_name="api", signature=self.token
        )

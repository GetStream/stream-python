class Users(object):
    def __init__(self, client, token):
        self.client = client
        self.token = token

    def add(self, user_id, data=None, get_or_create=False):
        payload = dict(id=user_id, data=data)
        return self.client.post(
            "user/",
            service_name="api",
            signature=self.token,
            data=payload,
            params={"get_or_create": get_or_create},
        )

    def get(self, user_id):
        return self.client.get(
            "user/%s" % user_id, service_name="api", signature=self.token
        )

    def update(self, user_id, data=None):
        payload = dict(data=data)
        return self.client.put(
            "user/%s" % user_id,
            service_name="api",
            signature=self.token,
            data=payload,
        )

    def delete(self, user_id):
        return self.client.delete(
            "user/%s" % user_id, service_name="api", signature=self.token
        )

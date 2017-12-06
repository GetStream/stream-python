class Personalization(object):
    def __init__(self, client, token):
        """

        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

    def get(self, url, **params):
        """
        Get personalized activities for this feed
        :param url: personalized url endpoint i.e "follow recommendations"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: personalized feed

        **Example**::

            personalization.get('follow_recommendations', user_id=123, limit=10, offset=10)
        """

        response = self.client.get(url, personal=True, params=params,
                                   signature=self.token)
        return response

    def post(self, url, **params):
        """
        "Generic function to post data to personalization endpoint
        :param url: personalized url endpoint i.e "follow recommendations"
        :param params: params to pass to url (data is a reserved keyword to post to body)

        """

        data = params['data'] or None

        response = self.client.post(url, personal=True, params=params,
                                    signature=self.token, data=data)
        return response

    def delete(self, url, **params):
        """
        shortcut to delete metadata or activites
        :param url: personalized url endpoint typical "meta"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: http response
        """

        response = self.client.delete(url, personal=True, params=params,
                                      signature=self.token)

        return response

    def upsert_data(self, collection_name, data):
        """

        :param collection_name: Collection Name i.e 'user'
        :param data: list of dictionaries
        :return: http response, 201 if successful along with data posted.

        **Example**::
            personalization.upsert_data('user', [{"id": 1, "name": "Juniper", "hobbies": ["Playing", "Sleeping", "Eating"]},
                                             {"id": 2, "name": "Ruby", "interests": ["Sunbeams", "Surprise Attacks"]}])
        """

        if type(data) != list:
            data = [data]

        ids = [i['id'] for i in data]

        # format data to expected json blob
        data_json = {}
        for i in range(len(ids)):
            data_json['%s:%s' % (collection_name, ids[i])] = data[i]

        response = self.post("meta", data={'data': data_json})

        return response

    def select_data(self, collection_name, ids):
        """

        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids of feed group i.e [123,456]
        :return: meta data as json blob

        **Example**::
            personalization.select_data('user', 1)
            personalization.select_data('user', [1,2,3])
        """

        if type(ids) != list:
            ids = [ids]

        foreign_ids = []
        for i in range(len(ids)):
            foreign_ids.append('%s:%s' % (collection_name, ids[i]))

        response = self.get('meta', foreign_ids=foreign_ids)

        return response

    def delete_data(self, collection_name, ids):
        """

        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids to delete i.e [123,456]
        :return:
        """

        if type(ids) != list:
            ids = [ids]

        foreign_ids = []
        for i in range(len(ids)):
            foreign_ids.append('%s:%s' % (collection_name, ids[i]))

        response = self.delete('meta', foreign_ids=foreign_ids)

        return response


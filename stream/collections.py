class Collections(object):

    def __init__(self, client, token):
        """
        Used to manipulate data at the 'meta' endpoint
        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

    def upsert(self, collection_name, data):
        """
        "Insert new or update existing data.
        :param collection_name: Collection Name i.e 'user'
        :param data: list of dictionaries
        :return: http response, 201 if successful along with data posted.

        **Example**::
            client.collection.upsert('user', [{"id": '1', "name": "Juniper", "hobbies": ["Playing", "Sleeping", "Eating"]},
                                           {"id": '2', "name": "Ruby", "interests": ["Sunbeams", "Surprise Attacks"]}])
        """

        if type(data) != list:
            data = [data]

        data_json = {collection_name: data}

        response = self.client.post('meta/', service_name='api',
                                    signature=self.token, data={'data': data_json})
        return response

    def select(self, collection_name, ids):
        """
        Retrieve data from meta endpoint, can include data you've uploaded or personalization/analytic data
        created by the stream team.
        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids of feed group i.e [123,456]
        :return: meta data as json blob

        **Example**::
            client.collection.select('user', 1)
            client.collection.select('user', [1,2,3])
        """

        if type(ids) != list:
            ids = [ids]
        ids = [str(i) for i in ids]

        foreign_ids = []
        for i in range(len(ids)):
            foreign_ids.append('%s:%s' % (collection_name, ids[i]))
        foreign_ids = ','.join(foreign_ids)

        response = self.client.get('meta/', service_name='api', params={'foreign_ids': foreign_ids},
                                   signature=self.token)

        return response

    def delete(self, collection_name, ids):
        """
        Delete data from meta.
        :param collection_name: Collection Name i.e 'user'
        :param ids: list of ids to delete i.e [123,456]
        :return: data that was deleted if successful or not.

        **Example**::
            client.collections.delete('user', '1')
            collections.delete('user', ['1','2','3'])
        """

        if type(ids) != list:
            ids = [ids]
        ids = [str(i) for i in ids]

        params = {'collection_name': collection_name, 'ids': ids}

        response = self.client.delete('meta/', service_name='api', params=params,
                                      signature=self.token)

        return response

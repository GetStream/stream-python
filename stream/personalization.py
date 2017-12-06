
class Personalization(object):
    def __init__(self, client, token):

        self.client = client
        self.token = token

    def get(self, url, **params):
        """
        Get personalized activities for this feed

        :param params:
        :return:
        """

        response = self.client.get(url, personal=True, params=params,
                                   signature=self.token)
        return response

    def post(self, url, *args, **params):
        """
        "Generic function to post data to personalization endpoint
        :param url: personalization endpoint ex: "meta"
        :param args: If endpoint has required args insert them here.
        :param kwargs: data is a reserved keyword to post to body

        """

        args = args or None
        data = params['data'] or None
        print(data)
        if args is not None:
            url = url + '/' + '/'.join(list(args))

        response = self.client.post(url, personal=True, params=params,
                                    signature=self.token, data=data)
        return response

    def upsert_data(self, item_type, ids, data):

        if type(ids) != list:
            ids = [ids]
        if type(data) != list:
            data = [data]

        assert len(ids) == len(data), "number of ids must match number of data points"

        # format data to expected json blob
        data_json = {}
        for i in range(len(ids)):
            data_json['%s:%s' % (item_type, ids[i])] = data[i]

        response = self.post("meta", data={'data': data_json})

        return response

    def select_data(self, item_type, ids):

        if type(ids) != list:
            ids = [ids]

        foreign_ids = []
        for i in range(len(ids)):
            foreign_ids.append('%s:%s' % (item_type, ids[i]))

        response = self.get('meta', foreign_ids=foreign_ids)

        return response



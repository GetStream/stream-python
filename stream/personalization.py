class Personalization(object):
    def __init__(self, client, token):
        """
        Methods to interact with personalized feeds.
        :param client: the api client
        :param token: the token
        """

        self.client = client
        self.token = token

    def get(self, resource, **params):
        """
        Get personalized activities for this feed
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: personalized feed

        **Example**::
            personalization.get('follow_recommendations', user_id=123, limit=10, offset=10)
        """

        response = self.client.get(resource, service_name='personalization', params=params,
                                   signature=self.token)
        return response

    def post(self, resource, **params):
        """
        "Generic function to post data to personalization endpoint
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url (data is a reserved keyword to post to body)


        **Example**::
            #Accept or reject recommendations.
            personalization.post('follow_recommendations', user_id=123, accepted=[123,345],
            rejected=[456])
        """

        data = params['data'] or None

        response = self.client.post(resource, service_name='personalization', params=params,
                                    signature=self.token, data=data)
        return response

    def delete(self, resource, **params):
        """
        shortcut to delete metadata or activites
        :param resource: personalized url endpoint typical "meta"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: data that was deleted if if successful or not.
        """

        response = self.client.delete(resource, service_name='personalization', params=params,
                                      signature=self.token)

        return response

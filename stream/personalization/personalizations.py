from stream.personalization.base import BasePersonalization


class Personalization(BasePersonalization):
    def get(self, resource, **params):
        """
        Get personalized activities for this feed
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: personalized feed

        **Example**::
            personalization.get('follow_recommendations', user_id=123, limit=10, offset=10)
        """

        return self.client.get(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    def post(self, resource, **params):
        """
        Generic function to post data to personalization endpoint
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url (data is a reserved keyword to post to body)


        **Example**::
            #Accept or reject recommendations.
            personalization.post('follow_recommendations', user_id=123, accepted=[123,345],
            rejected=[456])
        """

        data = params["data"] or None

        return self.client.post(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
            data=data,
        )

    def delete(self, resource, **params):
        """
        shortcut to delete metadata or activities
        :param resource: personalized url endpoint typical "meta"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: data that was deleted if successful or not.
        """

        return self.client.delete(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )


class AsyncPersonalization(BasePersonalization):
    async def get(self, resource, **params):
        """
        Get personalized activities for this feed
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: personalized feed

        **Example**::
            personalization.get('follow_recommendations', user_id=123, limit=10, offset=10)
        """

        return await self.client.get(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

    async def post(self, resource, **params):
        """
        Generic function to post data to personalization endpoint
        :param resource: personalized resource endpoint i.e "follow_recommendations"
        :param params: params to pass to url (data is a reserved keyword to post to body)


        **Example**::
            #Accept or reject recommendations.
            personalization.post('follow_recommendations', user_id=123, accepted=[123,345],
            rejected=[456])
        """

        data = params["data"] or None

        return await self.client.post(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
            data=data,
        )

    async def delete(self, resource, **params):
        """
        shortcut to delete metadata or activities
        :param resource: personalized url endpoint typical "meta"
        :param params: params to pass to url i.e user_id = "user:123"
        :return: data that was deleted if successful or not.
        """

        return await self.client.delete(
            resource,
            service_name=self.SERVICE_NAME,
            params=params,
            signature=self.token,
        )

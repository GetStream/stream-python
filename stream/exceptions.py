

class StreamApiException(Exception):

    def __init__(self, error_message, status_code=None):
        Exception.__init__(self, error_message)
        self.detail = error_message
        if status_code is not None:
            self.status_code = status_code

    code = 1

    def __repr__(self):
        return '%s (%s)' % (self.__class__.__name__, self.detail)

    def __unicode__(self):
        return '%s (%s)' % (self.__class__.__name__, self.detail)


class ApiKeyException(StreamApiException):

    '''
    Raised when there is an issue with your Access Key
    '''
    status_code = 401
    code = 2


class SignatureException(StreamApiException):

    '''
    Raised when there is an issue with the signature you provided
    '''
    status_code = 401
    code = 3


class InputException(StreamApiException):

    '''
    Raised when you send the wrong data to the API
    '''
    status_code = 400
    code = 4


class CustomFieldException(StreamApiException):

    '''
    Raised when there are missing or misconfigured custom fields
    '''
    status_code = 400
    code = 5


class FeedConfigException(StreamApiException):

    '''
    Raised when there are missing or misconfigured custom fields
    '''
    status_code = 400
    code = 6


class SiteSuspendedException(StreamApiException):

    '''
    Raised when the site requesting the data is suspended
    '''
    status_code = 401
    code = 7

class InvalidPaginationException(StreamApiException):

    '''
    Raised when there is an issue with your Access Key
    '''
    status_code = 401
    code = 8


class MissingRankingException(FeedConfigException):
    '''
    Raised when you didn't configure the ranking for the given feed
    '''
    status_code = 400
    code = 12


class MissingUserException(MissingRankingException):
    status_code = 400
    code = 10


class RankingException(FeedConfigException):
    '''
    Raised when there is a runtime issue with ranking the feed
    '''
    status_code = 400
    code = 11


class RateLimitReached(StreamApiException):

    '''
    Raised when too many requests are performed
    '''
    status_code = 429
    code = 9


class OldStorageBackend(StreamApiException):
    '''
    Raised if you try to perform an action which only works with the new storage
    '''
    status_code = 400
    code = 13


class BestPracticeException(StreamApiException):
    '''
    Raised if best practices are enforced and you do something that
    would break a high volume integration
    '''
    status_code = 400
    code = 15


class DoesNotExistException(StreamApiException):
    '''
    Raised when the requested resource could not be found.
    '''
    status_code = 404
    code = 16


class NotAllowedException(StreamApiException):
    '''
    Raised when the requested action is not allowed for some reason.
    '''
    status_code = 403
    code = 17


def get_exceptions():
    from stream import exceptions
    classes = []
    for k in dir(exceptions):
        a = getattr(exceptions, k)
        try:
            if a and issubclass(a, StreamApiException):
                classes.append(a)
        except TypeError:
            pass
    return classes


def get_exception_dict():
    exception_dict = {}
    for c in get_exceptions():
        exception_dict[c.code] = c
    return exception_dict

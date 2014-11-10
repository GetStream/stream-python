import hmac
import hashlib
import base64


def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b'=')


def sign(api_secret, feed_id):
    '''
    Base64 encoded sha1 signature

    :param secret: the secret
    :param feed_id: the feed_id to sign (commonly a feed id such as user:1)

    **Example**::
        signature = sign('secret', 'user:1')

    '''
    key = hashlib.sha1((api_secret).encode('utf-8')).digest()
    signed = hmac.new(key, msg=feed_id.encode('utf8'), digestmod=hashlib.sha1)
    digest = signed.digest()
    urlsafe_digest = b64_encode(digest)
    token = urlsafe_digest.decode('ascii')
    return token

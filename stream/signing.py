import hmac
import hashlib
import base64


def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b'=')

def sign(api_secret, feed_id):
    '''
    Base64 encoded sha1 signature

    :param api_secret: the api secret
    :param feed_id: the feed_id to sign (commonly a feed id such as user1)

    **Example**::
        signature = sign('secret', 'user1')

    '''
    hashed_secret = hashlib.sha1((api_secret).encode('utf-8')).digest()
    signed = hmac.new(
        hashed_secret, msg=feed_id.encode('utf8'), digestmod=hashlib.sha1)
    digest = signed.digest()
    urlsafe_digest = b64_encode(digest)
    token = urlsafe_digest.decode('ascii')
    return token


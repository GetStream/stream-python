import hmac
import hashlib
import base64


def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b'=')


class StreamSigner(object):

    '''
    Simplified stream signer which doesnt rely on Django
    
    **Example**::
        signature = StreamSigner(secret).sign(feed)
    
    In essence it does
    - hmac.new
    - base64 encoded
    '''

    def __init__(self, secret):
        self.secret = secret

    def signature(self, value):
        key = hashlib.sha1((self.secret).encode('utf-8')).digest()
        signed = hmac.new(key, msg=str(value), digestmod=hashlib.sha1)
        signature = b64_encode(signed.digest())
        return str(signature)



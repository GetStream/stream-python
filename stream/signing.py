import hmac
import hashlib
import base64


def b64_encode(s):
    return base64.urlsafe_b64encode(s).strip(b'=')


def sign(secret, value):
    '''
    Base64 encoded sha1 signature
    
    :param secret: the secret
    :param value: the value to sign (commonly a feed id such as user:1)
    
    **Example**::
        signature = sign('secret', 'user:1')
    
    '''
    key = hashlib.sha1((secret).encode('utf-8')).digest()
    signed = hmac.new(key, msg=str(value), digestmod=hashlib.sha1)
    signature = b64_encode(signed.digest())
    return str(signature)



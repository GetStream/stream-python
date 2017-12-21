#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import unittest

from stream.httpsig.sign import HeaderSigner, Signer
from stream.httpsig.verify import HeaderVerifier, Verifier

class BaseTestCase(unittest.TestCase):
    def _parse_auth(self, auth):
        """Basic Authorization header parsing."""
        # split 'Signature kvpairs'
        s, param_str = auth.split(' ', 1)
        self.assertEqual(s, 'Signature')
        # split k1="v1",k2="v2",...
        param_list = param_str.split(',')
        # convert into [(k1,"v1"), (k2, "v2"), ...]
        param_pairs = [p.split('=', 1) for p in param_list]
        # convert into {k1:v1, k2:v2, ...}
        param_dict = {}
        for k, v in param_pairs:
            param_dict[k] = v.strip('"')
        return param_dict


class TestVerifyHMACSHA1(BaseTestCase):
    def setUp(self):
        secret = b"something special goes here"

        self.keyId = "Test"
        self.algorithm = "hmac-sha1"
        self.sign_secret = secret
        self.verify_secret = secret

    def test_basic_sign(self):
        signer = Signer(secret=self.sign_secret, algorithm=self.algorithm)
        verifier = Verifier(secret=self.verify_secret, algorithm=self.algorithm)

        GOOD = b"this is a test"
        BAD = b"this is not the signature you were looking for..."

        # generate signed string
        signature = signer._sign(GOOD)
        self.assertTrue(verifier._verify(data=GOOD, signature=signature))
        self.assertFalse(verifier._verify(data=BAD, signature=signature))

    def test_default(self):
        unsigned = {
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT'
        }

        hs = HeaderSigner(key_id="Test", secret=self.sign_secret, algorithm=self.algorithm)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(headers=signed, secret=self.verify_secret)
        self.assertTrue(hv.verify())

    def test_signed_headers(self):
        HOST = "example.com"
        METHOD = "POST"
        PATH = '/foo?param=value&pet=dog'
        hs = HeaderSigner(key_id="Test", secret=self.sign_secret, algorithm=self.algorithm, headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'content-md5',
            'content-length'
        ])
        unsigned = {
            'Host': HOST,
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT',
            'Content-Type': 'application/json',
            'Content-MD5': 'Sd/dVLAcvNLSq16eXua5uQ==',
            'Content-Length': '18',
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)

        hv = HeaderVerifier(headers=signed, secret=self.verify_secret, host=HOST, method=METHOD, path=PATH)
        self.assertTrue(hv.verify())

    def test_incorrect_headers(self):
        HOST = "example.com"
        METHOD = "POST"
        PATH = '/foo?param=value&pet=dog'
        hs = HeaderSigner(secret=self.sign_secret,
                          key_id="Test",
                          algorithm=self.algorithm,
                          headers=[
                            '(request-target)',
                            'host',
                            'date',
                            'content-type',
                            'content-md5',
                            'content-length'])
        unsigned = {
            'Host': HOST,
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT',
            'Content-Type': 'application/json',
            'Content-MD5': 'Sd/dVLAcvNLSq16eXua5uQ==',
            'Content-Length': '18',
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)

        hv = HeaderVerifier(headers=signed, secret=self.verify_secret, required_headers=["some-other-header"], host=HOST, method=METHOD, path=PATH)
        self.assertRaises(Exception, hv.verify)

    def test_extra_auth_headers(self):
        HOST = "example.com"
        METHOD = "POST"
        PATH = '/foo?param=value&pet=dog'
        hs = HeaderSigner(key_id="Test", secret=self.sign_secret, algorithm=self.algorithm, headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'content-md5',
            'content-length'
        ])
        unsigned = {
            'Host': HOST,
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT',
            'Content-Type': 'application/json',
            'Content-MD5': 'Sd/dVLAcvNLSq16eXua5uQ==',
            'Content-Length': '18',
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)
        hv = HeaderVerifier(headers=signed, secret=self.verify_secret, method=METHOD, path=PATH, required_headers=['date', '(request-target)'])
        self.assertTrue(hv.verify())


class TestVerifyHMACSHA256(TestVerifyHMACSHA1):
    def setUp(self):
        super(TestVerifyHMACSHA256, self).setUp()
        self.algorithm = "hmac-sha256"

class TestVerifyHMACSHA512(TestVerifyHMACSHA1):
    def setUp(self):
        super(TestVerifyHMACSHA512, self).setUp()
        self.algorithm = "hmac-sha512"


class TestVerifyRSASHA1(TestVerifyHMACSHA1):
    def setUp(self):
        private_key_path = os.path.join(os.path.dirname(__file__), 'rsa_private.pem')
        with open(private_key_path, 'rb') as f:
            private_key = f.read()

        public_key_path = os.path.join(os.path.dirname(__file__), 'rsa_public.pem')
        with open(public_key_path, 'rb') as f:
            public_key = f.read()

        self.keyId = "Test"
        self.algorithm = "rsa-sha1"
        self.sign_secret = private_key
        self.verify_secret = public_key

class TestVerifyRSASHA256(TestVerifyRSASHA1):
    def setUp(self):
        super(TestVerifyRSASHA256, self).setUp()
        self.algorithm = "rsa-sha256"

class TestVerifyRSASHA512(TestVerifyRSASHA1):
    def setUp(self):
        super(TestVerifyRSASHA512, self).setUp()
        self.algorithm = "rsa-sha512"

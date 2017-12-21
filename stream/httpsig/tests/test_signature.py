#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import json
import unittest

import stream.httpsig.sign as sign
from stream.httpsig.utils import parse_authorization_header


class TestSign(unittest.TestCase):
    DEFAULT_SIGN_ALGORITHM = sign.DEFAULT_SIGN_ALGORITHM

    def setUp(self):
        sign.DEFAULT_SIGN_ALGORITHM = "rsa-sha256"
        self.key_path = os.path.join(os.path.dirname(__file__), 'rsa_private.pem')
        with open(self.key_path, 'rb') as f:
            self.key = f.read()

    def tearDown(self):
        sign.DEFAULT_SIGN_ALGORITHM = self.DEFAULT_SIGN_ALGORITHM

    def test_default(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key)
        unsigned = {
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT'
        }
        signed = hs.sign(unsigned)
        self.assertTrue('Date' in signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertTrue('Authorization' in signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertTrue('keyId' in params)
        self.assertTrue('algorithm' in params)
        self.assertTrue('signature' in params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'rsa-sha256')
        self.assertEqual(params['signature'], 'ATp0r26dbMIxOopqw0OfABDT7CKMIoENumuruOtarj8n/97Q3htHFYpH8yOSQk3Z5zh8UxUym6FYTb5+A0Nz3NRsXJibnYi7brE/4tx5But9kkFGzG+xpUmimN4c3TMN7OFH//+r8hBf7BT9/GmHDUVZT2JzWGLZES2xDOUuMtA=')

    def test_all(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key, headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'content-md5',
            'content-length'
        ])
        unsigned = {
            'Host': 'example.com',
            'Date': 'Thu, 05 Jan 2012 21:31:40 GMT',
            'Content-Type': 'application/json',
            'Content-MD5': 'Sd/dVLAcvNLSq16eXua5uQ==',
            'Content-Length': '18',
        }
        signed = hs.sign(unsigned, method='POST', path='/foo?param=value&pet=dog')

        self.assertTrue('Date' in signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertTrue('Authorization' in signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertTrue('keyId' in params)
        self.assertTrue('algorithm' in params)
        self.assertTrue('signature' in params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'rsa-sha256')
        self.assertEqual(params['headers'], '(request-target) host date content-type content-md5 content-length')
        self.assertEqual(params['signature'], 'G8/Uh6BBDaqldRi3VfFfklHSFoq8CMt5NUZiepq0q66e+fS3Up3BmXn0NbUnr3L1WgAAZGplifRAJqp2LgeZ5gXNk6UX9zV3hw5BERLWscWXlwX/dvHQES27lGRCvyFv3djHP6Plfd5mhPWRkmjnvqeOOSS0lZJYFYHJz994s6w=')

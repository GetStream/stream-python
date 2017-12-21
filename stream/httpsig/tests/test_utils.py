#!/usr/bin/env python
import os
import re
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from stream.httpsig.utils import get_fingerprint

class TestUtils(unittest.TestCase):

    def test_get_fingerprint(self):
        with open(os.path.join(os.path.dirname(__file__), 'rsa_public.pem'), 'r') as k:
            key = k.read()
        fingerprint = get_fingerprint(key)
        self.assertEqual(fingerprint, "73:61:a2:21:67:e0:df:be:7e:4b:93:1e:15:98:a5:b7")

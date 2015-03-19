# -*- coding: utf-8 -*-

from django.test import TestCase
from django.core import mail


class DBMailTestCase(TestCase):
    def setUp(self):
        pass

    def test_simple(self):
        self.assertEqual(1, 1)

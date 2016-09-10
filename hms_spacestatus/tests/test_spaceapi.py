import unittest
from unittest.mock import Mock

import requests
from requests.exceptions import ConnectionError, SSLError

from hms_spacestatus.spaceapi import SpaceApi


def prepare_response(state):
    resp = requests.Response()
    resp.status_code = 200
    resp.json = Mock(return_value={'state': {'open': state}})
    return resp


class SpaceApiTest(unittest.TestCase):

    def setUp(self):
        self.spaceapi = SpaceApi()

    def test_api_open(self):
        """Test that the API is open when correct HTTP answer arrives"""
        requests.get = Mock(return_value=prepare_response(True))

        self.assertTrue(self.spaceapi.is_open())
        self.assertFalse(self.spaceapi.ssl_error)
        self.assertFalse(self.spaceapi.crash_error)

    def test_api_closed(self):
        """Test that the API is closed when correct HTTP answer arrives"""
        requests.get = Mock(return_value=prepare_response(False))

        self.assertFalse(self.spaceapi.is_open())
        self.assertFalse(self.spaceapi.ssl_error)
        self.assertFalse(self.spaceapi.crash_error)

    def test_api_ssl_error(self):
        """Test that API bad certificate does not crash the program."""
        resp = prepare_response(True)
        requests.get = Mock(side_effect=[SSLError(), resp])

        self.assertTrue(self.spaceapi.is_open())
        self.assertTrue(self.spaceapi.ssl_error)
        self.assertFalse(self.spaceapi.crash_error)

    def test_api_http_error(self):
        """Test that API crash does not crash the program."""
        requests.get = Mock(side_effect=ConnectionError('test'))

        self.assertFalse(self.spaceapi.is_open())
        self.assertTrue(self.spaceapi.crash_error)

    def test_api_ssl_http_error(self):
        """Test that SSL error + API crash does not crash the program."""
        requests.get = Mock(side_effect=[SSLError(), ConnectionError('test')])

        self.assertFalse(self.spaceapi.is_open())
        self.assertTrue(self.spaceapi.crash_error)
        self.assertTrue(self.spaceapi.ssl_error)
import unittest
from unittest.mock import Mock
import json

import requests
from requests.exceptions import ConnectionError, SSLError

from hms_spacestatus import settings
from hms_spacestatus.spaceapi import SpaceApi, RequestShield,\
    SPACEAPI_SENSOR_URL


def prepare_response(state):
    resp = requests.Response()
    resp.status_code = 200
    resp.json = Mock(return_value={'state': {'open': state}})
    return resp

def prepare_empty_response():
    resp = requests.Response()
    resp.status_code = 200
    return resp

def prepare_sensor_data(state):
    expected_data = {
        'key': settings.SPACEAPI_KEY,
        'sensors': json.dumps({"state": {"open": state}})
    }
    return expected_data

class RequestShieldTest(unittest.TestCase):

    """Tests against custom HTTP request exception shield."""

    def setUp(self):
        self.reqshield = RequestShield()

    def test_api_ssl_error(self):
        """Test that API bad certificate does not crash the program."""
        resp = prepare_response(True)
        requests.get = Mock(side_effect=[SSLError(), resp])

        result = self.reqshield(requests.get, "https://example.com")

        self.assertEqual(result, resp)
        self.assertTrue(self.reqshield.ssl_error)

    def test_api_http_error(self):
        """Test that a bad HTTP code does not crash the program."""
        resp = prepare_response(True)
        resp.status_code = 500
        requests.get = Mock(return_value=resp)

        result = self.reqshield(requests.get, "http://example.com")

        self.assertIsNone(result)
        self.assertTrue(self.reqshield.bad_http_code)

    def test_api_connection_error(self):
        """Test that API crash does not crash the program."""
        requests.get = Mock(side_effect=ConnectionError('test'))
        result = self.reqshield(requests.get, "http://example.com")

        self.assertIsNone(result)
        self.assertTrue(self.reqshield.crash_error)

    def test_api_ssl_connection_error(self):
        """Test that SSL error + API crash does not crash the program."""
        requests.get = Mock(side_effect=[SSLError(), ConnectionError('test')])

        result = self.reqshield(requests.get, "http://example.com")

        self.assertIsNone(result)
        self.assertTrue(self.reqshield.crash_error)
        self.assertTrue(self.reqshield.ssl_error)


class SpaceApiTest(unittest.TestCase):

    """Tests against the SpaceAPI wrapper class."""

    def setUp(self):
        self.spaceapi = SpaceApi()

    def test_api_is_open(self):
        """Test that the API is open when correct HTTP answer arrives"""
        requests.get = Mock(return_value=prepare_response(True))
        self.assertTrue(self.spaceapi.is_open())

    def test_api_is_open_crash(self):
        requests.get = Mock(side_effect=ConnectionError('test'))
        self.assertFalse(self.spaceapi.is_open())

    def test_api_is_closed(self):
        """Test that the API is closed when correct HTTP answer arrives"""
        requests.get = Mock(return_value=prepare_response(False))
        self.assertFalse(self.spaceapi.is_open())

    def test_api_open(self):
        """Test to open the hackerspace using the API."""
        requests.post = Mock(return_value=prepare_empty_response())

        self.spaceapi.open()

        requests.post.assert_called_once_with(
            SPACEAPI_SENSOR_URL, data=prepare_sensor_data(True))

    def test_api_close(self):
        """Test to close the hackerspace using the API."""
        requests.post = Mock(return_value=prepare_empty_response())

        self.spaceapi.close()

        requests.post.assert_called_once_with(
            SPACEAPI_SENSOR_URL, data=prepare_sensor_data(False))

    def test_api_toggle(self):
        requests.get = Mock(return_value=prepare_response(True))
        requests.post = Mock(return_value=prepare_empty_response())

        self.spaceapi.toggle()

        requests.post.assert_called_once_with(
            SPACEAPI_SENSOR_URL, data=prepare_sensor_data(False))

        requests.get = Mock(return_value=prepare_response(False))
        requests.post = Mock(return_value=prepare_empty_response())

        self.spaceapi.toggle()

        requests.post.assert_called_once_with(
            SPACEAPI_SENSOR_URL, data=prepare_sensor_data(True))

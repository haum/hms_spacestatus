import logging
import json

import requests
from requests.exceptions import SSLError, RequestException

from hms_spacestatus import settings

# Constants

SPACEAPI_STATUS_URL = "https://spaceapi.net/new/space/haum/status/json"
SPACEAPI_SENSOR_URL = "https://spaceapi.net/new/space/haum/sensor/set"


def get_logger():
    return logging.getLogger(__name__)


class RequestShield:

    """Class for securing HTTP call from exceptions.

    This class uses advanced Python and may be difficult to understand at first.

    Basically it allows to perform requests using the requests Python module,
    but handles possible errors and set flags depending on the error type in
    order to report it later.

    Here is basic usage, when the HTTP server is functional:

    >>> shield = RequestShield()
    >>> shield(requests.get, "http://example.com")
    <Response [200]>

    However, if the HTTP server has problems, we get a None value and we can
    read the flags to check what the error is:

    >>> shield = RequestShield()
    >>> shield(requests.get, "http://example.com")
    None
    >>> shield.ssl_error
    True
    >>> shield.crash_error
    False

    And that's it for this class.

    It was written apart from the SpaceAPI class because of SRP (single
    responsibility principle).

    """

    def __init__(self):
        self.ssl_error = False
        self.crash_error = False
        self.bad_http_code = False

    def _unsafe_req(self, req, *args, **kwargs):
        """Perform an unsafe HTTP request, but try safe first."""
        try:
            # Try normal request
            self.ssl_error = False
            return req(*args, **kwargs)

        except SSLError:
            # If SSL error, retry without verification (this is bad)

            get_logger().warning(
                "Bad certificate for SpaceAPI, retrying without verification")

            self.ssl_error = True
            kwargs['verify'] = False
            return req(*args, **kwargs)

    def _nocrash_req(self, *args, **kwargs):
        """Perform an HTTP request and catch request exception."""
        try:
            # Perform unsafe request
            self.crash_error = False
            r = self._unsafe_req(*args, **kwargs)

            # Check status code
            if r.status_code != 200:
                self.bad_http_code = True

                get_logger().warning('HTTP status code {} for SpaceAPI {}'
                                     .format(r.status_code, r.url))

                # If we have a bad status code, the JSON response have great
                # chances of being incorrect, so we prefer to return empty
                # response.
                return None

            # And finally return the request
            return r

        except RequestException as e:
            # Catch whatever possible HTTP exception because we do not want a
            # global crash because of spaceapi.

            get_logger().error('SpaceAPI request error : {} {}'.format(
                e.__class__.__name__, e))

            # Save the error
            self.crash_error = True

            # Return nothing (to be handled by methods using this call)
            return None

    def __call__(self, *args, **kwargs):
        """Perform an HTTP request and catch whatever possible HTTP error."""
        return self._nocrash_req(*args, **kwargs)


class SpaceApi:

    """Class handling interactions with SpaceAPI."""

    def __init__(self):
        self.reqshield = RequestShield()

    # Methods to interact with the API

    def _set_status(self, state):
        """Set the status of the hackerspace."""

        # Prepare data to be sent
        sensors_payload = json.dumps({'state': {'open': state}})
        data = {'key': settings.SPACEAPI_KEY, 'sensors': sensors_payload}

        # Perform POST request
        self.reqshield(requests.post, SPACEAPI_SENSOR_URL, data=data)


    def _get_status(self):
        return self.reqshield(requests.get, SPACEAPI_STATUS_URL)

    # We wrote the hardest part, now we can use these low level methods in some
    # higher level methods.

    def is_open(self):
        """Check if the space is open."""
        req = self._get_status()

        # Handle possible crash
        if not req:
            return False

        dct = req.json()
        return dct['state']['open']

    def set_state(self, state):
        """Set the space status."""
        self._set_status(state)

    def open(self):
        """Opens the space."""
        self.set_state(True)

    def close(self):
        """Close the space."""
        self.set_state(False)

    def toggle(self):
        """Toggle the space, use with caution."""
        if self.is_open():
            self.close()
        else:
            self.open()

# If we start this file, we try to toggle the space status to check that the
# API key is working.

if __name__ == '__main__':
    s = SpaceApi()
    s.toggle()
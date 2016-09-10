import logging
import json

import requests
from requests.exceptions import SSLError

from hms_spacestatus import settings

# Constants

SPACEAPI_STATUS_URL = "https://spaceapi.net/new/space/haum/status/json"
SPACEAPI_SENSOR_URL = "https://spaceapi.net/new/space/haum/sensor/set"


def get_logger():
    return logging.getLogger(__name__)


class SpaceApi:

    """Class handling interactions with SpaceAPI."""

    def _unsafe_req(self, req, *args, **kwargs):
        """Perform an unsafe HTTP request, but try safe first."""
        try:
            # Try normal request
            return req(*args, **kwargs)

        except SSLError:
            # If SSL error, retry without verification (this is bad)

            get_logger().warning(
                "Bad certificate for SpaceAPI, retrying without verification")

            kwargs['verify'] = False
            return req(*args, **kwargs)

    def _set_status(self, state):
        """Set the status of the hackerspace."""

        # Prepare data to be sent

        sensors_payload = json.dumps({'state': {'open': state}})
        data = {'key': settings.SPACEAPI_KEY, 'sensors': sensors_payload}

        # Perform POST request
        r = self._unsafe_req(
            requests.post, SPACEAPI_SENSOR_URL,
            data=data)

        # Check status code
        if r.status_code != 200:
            get_logger().error('HTTP status code {} for set status'
                               .format(r.status_code))

    def _get_status(self):
        r = self._unsafe_req(requests.get, SPACEAPI_STATUS_URL)

        if r.status_code != 200:
            get_logger().error('HTTP status code {} for get status'
                               .format(r.status_code))

        return r

    # We wrote the hardest part, now we can use these low level methods in some
    # higher level methods.

    def is_open(self):
        """Check if the space is open."""
        dct = self._get_status().json()
        return dct['state']['open']

    def open(self):
        """Opens the space."""
        self._set_status(True)

    def close(self):
        """Close the space."""
        self._set_status(False)

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
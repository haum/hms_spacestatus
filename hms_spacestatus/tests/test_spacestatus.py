import unittest
from unittest.mock import Mock

from hms_spacestatus.spacestatus import SpaceStatus


class SpaceStatusChangedTest(unittest.TestCase):

    def setUp(self):
        self.spstatus = SpaceStatus('/tmp/fake')
        self.callback = Mock()
        self.spstatus.state_changed_listenners.append(self.callback)

    def test_changed_state(self):
        self.spstatus.previous_state = False
        self.spstatus.read_state = Mock(return_value=True)

        result = self.spstatus.check_changed_state(None)

        self.assertTrue(result)
        self.callback.assert_called_once_with(True)

    def test_not_changed_state(self):
        self.spstatus.previous_state = True
        self.spstatus.read_state = Mock(return_value=True)

        result = self.spstatus.check_changed_state(None)

        self.assertFalse(result)
        self.callback.assert_not_called()
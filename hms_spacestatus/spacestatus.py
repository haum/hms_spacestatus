from os import path
import logging


def get_logger():
    return logging.getLogger(__name__)


class SpaceStatus:
    def __init__(self, filepath):
        """Default constructor."""
        self.dirpath = path.dirname(filepath)
        self.filepath = filepath
        self.previous_state = self.read_state()
        self.state_changed_listenners = []

    def set_state(self, new_state):
        """Set the current state of the API."""

        get_logger().info("Writting new state {}...".format(new_state))

        with open(self.filepath, 'w') as f:
            f.write('1' if new_state else '0')

        get_logger().info("Written new state {}.".format(new_state))

    def read_state(self):
        """Read the current state.

        Returns:
            bool: True if the state is open, False otherwise

        """
        get_logger().info("Reading status file {}...".format(self.filepath))

        try:
            with open(self.filepath, 'r') as f:
                return f.read().strip() == "1"

        except FileNotFoundError:
            get_logger().error("Status file not found! ({})".format(self.filepath))
            return False

    def check_changed_state(self, event):
        """Check if the state has changed and call listenners.

        Args:
            event: watchdog event

        Returns:
            bool: True if the state has changed and the listenners have been called,
            False otherwise.

        """
        state = self.read_state()

        if state != self.previous_state:
            self.previous_state = state

            get_logger().info("State has changed! Calling listenners...")

            for listenner in self.state_changed_listenners:
                listenner(state)

            return True

        return False
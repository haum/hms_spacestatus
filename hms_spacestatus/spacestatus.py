from os import path
import time
import logging

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

from hms_spacestatus import settings


def get_logger():
    return logging.getLogger(__name__)

class MyHandler(PatternMatchingEventHandler):

    """Handler for the watchdog library."""

    def __init__(self):
        super().__init__(patterns = ["*"])
        self.listenners = []

    def process(self, event):
        for listenner in self.listenners:
            listenner(event)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


class SpaceStatus:
    def __init__(self, filepath):
        """Default constructor."""
        self.dirpath = path.dirname(filepath)
        self.filepath = filepath
        self.previous_state = self.read_state()
        self.state_changed_listenners = []

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

    def monitor(self):
        """Start infinite monitoring of the state status."""
        get_logger().info("Initial state is {}".format(self.previous_state))
        get_logger().info("Staring file watchdog monitor...")

        event_handler = MyHandler()
        event_handler.listenners.append(self.check_changed_state)

        observer = Observer()
        observer.schedule(event_handler, self.dirpath, recursive=True)
        observer.start()

        get_logger().info("Started file watchdog monitor...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            get_logger().critical("Got a KeyboardInterrupt, stopping watchdog monitor...")
            observer.stop()

        observer.join()
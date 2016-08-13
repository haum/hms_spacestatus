import logging
import time

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


def get_logger():
    return logging.getLogger(__name__)


class MyHandler(PatternMatchingEventHandler):

    """Custom handler for the watchdog library.

    With this handler we want to monitor every file in a specific directory,
    but only file creation and modification.

    """

    def __init__(self):
        super().__init__(patterns = ["*"])
        self.listenners = []

    def process(self, event):
        """Process an event by calling all listeners with event as arg."""
        for listenner in self.listenners:
            listenner(event)

    def on_modified(self, event):
        self.process(event)

    def on_created(self, event):
        self.process(event)


class FileWatcher:
    def __init__(self, dirpath):
        """Default constructor."""
        self.dirpath = dirpath
        self.listeners = []

    def monitor(self):
        """Start infinite monitoring of the state status."""

        get_logger().info("Staring file watchdog monitor...")
        event_handler = MyHandler()

        # Rebind all listeners to the event handler
        for listener in self.listeners:
            event_handler.listenners.append(listener)

        # Create and start file observer
        observer = Observer()
        observer.schedule(event_handler, self.dirpath, recursive=True)
        observer.start()

        get_logger().info("Started file watchdog monitor...")

        # Infinite waiting loop
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            get_logger().critical(
                "Got a KeyboardInterrupt, stopping watchdog monitor...")
            observer.stop()

        observer.join()

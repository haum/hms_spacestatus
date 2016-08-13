import logging
import time

from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


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


class FileWatcher:
    def __init__(self, dirpath):
        self.dirpath = dirpath
        self.listeners = []

    def monitor(self):
        """Start infinite monitoring of the state status."""

        get_logger().info("Staring file watchdog monitor...")

        event_handler = MyHandler()

        for listener in self.listeners:
            event_handler.listenners.append(listener)

        observer = Observer()
        observer.schedule(event_handler, self.dirpath, recursive=True)
        observer.start()

        get_logger().info("Started file watchdog monitor...")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            get_logger().critical(
                "Got a KeyboardInterrupt, stopping watchdog monitor...")
            observer.stop()

        observer.join()

from os import path
import time
import logging
import inspect

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


class SpaceStatusIRC:
    def __init__(self, spacestatus, rabbit):
        self.spacestatus = spacestatus
        self.rabbit = rabbit

    def irc_debug(self, msg):
        self.rabbit.publish('irc_debug', {'privmsg': msg})

    def irc_command_listener(self, client, topic, dct):
        if dct['command'] == 'spacestatus':
            command_args_dirty = dct['arg'].split(' ')
            command_args = []

            for x in command_args_dirty:
                if x:
                    command_args.append(x)

            get_logger().info("Received spacestatus IRC command with args {}".format(command_args))

            if len(command_args) == 0:
                self.send_status()
            else:
                try:
                    method = getattr(self, 'on_{}'.format(command_args[0]))
                    method()
                except AttributeError:
                    self.irc_debug("Commande invalide")
                    self.on_help()

    def on_help(self):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        commands = [method[0] for method in filter(lambda x: x[0].startswith('on_'), methods)]
        commands_str = ', '.join(map(lambda x: x[3:], commands))
        self.irc_debug('Aide : !spacestatus [{}]'.format(commands_str))

    def on_open(self):
        if self.spacestatus.read_state():
            self.irc_debug('Attention : l’espace est déjà ouvert !'.format())
        self.spacestatus.set_state(True)

    def on_close(self):
        if not self.spacestatus.read_state():
            self.irc_debug('Attention : l’espace est déjà fermé !')
        self.spacestatus.set_state(False)

    def send_status(self):
        msg = 'L’espace est fermé !'
        if self.spacestatus.read_state():
            msg = 'L’espace est ouvert !'

        self.irc_debug(msg)

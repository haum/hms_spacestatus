import logging
from threading import Thread

import coloredlogs

from hms_base.client import Client
from hms_base.decorators import topic

from hms_spacestatus import settings
from hms_spacestatus.spacestatus import SpaceStatus
from hms_spacestatus.file_monitoring import FileWatcher

CHANGE_STATUS_COMMANDS = ['open', 'open_silent', 'close', 'close_silent', 'toggle', 'toggle_silent']


def get_logger():
    return logging.getLogger(__name__)


def main():
    """Entry point of the program."""

    # Logging
    coloredlogs.install(level='INFO')

    # Connect to Rabbit
    rabbit = Client('hms_spacestatus', settings.RABBIT_EXCHANGE,
                    settings.RABBIT_ROUTING_KEYS)

    rabbit.connect(settings.RABBIT_HOST)

    # SpaceStatus
    def state_changed(newstate):
        get_logger().info("State changed: {}".format(newstate))

        # Publish the space status change over RabbitMQ for other microservices
        rabbit.publish("spacestatus_state_changed", {"new_value": newstate})

    # SpaceStatus object
    spacestatus = SpaceStatus(settings.SPACESTATUS_FILE)
    spacestatus.state_changed_listenners.append(state_changed)

    get_logger().info("Initial state is {}".format(spacestatus.previous_state))

    # File monitoring
    filewacher = FileWatcher(spacestatus.dirpath)
    filewacher.listeners.append(spacestatus.check_changed_state)

    monitor_thread = Thread(target=filewacher.monitor)
    monitor_thread.setDaemon(True)

    get_logger().info("Starting file monitor thread...")
    monitor_thread.start()

    # Closure, cannot use @topic directly on method
    @topic('spacestatus.query')
    def query_closure(client, topic, dct):
        command = dct['command']

        if command == 'status':
            data = {'is_open':  spacestatus.read_state()}
            rabbit.publish('spacestatus.answer', data)

        elif command in CHANGE_STATUS_COMMANDS:
            # Check what the user wants to do
            if command.startswith('toggle'):
                will_open = not spacestatus.read_state()
            else:
                will_open = command.startswith('open')

            different_state = will_open != spacestatus.read_state()

            # Set the internal state
            spacestatus.set_state(will_open)

            # Send answer data using the message broker
            data = {
                'is_open': spacestatus.read_state(),
                'has_changed': different_state,
                'source': dct['source']
            }
            rabbit.publish('spacestatus.answer', data)

            # If new state and not silent, broadcast the status change
            if not command.endswith('silent') and different_state:
                rabbit.publish('spacestatus.broadcast', data)

    rabbit.listeners.append(query_closure)

    get_logger().info("Starting passive consumming...")
    rabbit.start_consuming()

    monitor_thread.join()

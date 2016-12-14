import logging
from threading import Thread

import coloredlogs

from hms_base.client import Client
from hms_base.decorators import topic

from hms_spacestatus import settings
from hms_spacestatus.spacestatus import SpaceStatus
from hms_spacestatus.irc import SpaceStatusIRC
from hms_spacestatus.file_monitoring import FileWatcher
from hms_spacestatus.spaceapi import SpaceApi


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

        # Register the new state on SpaceAPI
        #spaceapi.set_state(newstate)

        # Display the new state on irc and the state of SpaceAPI
        #spacestatus_irc.send_status()
        #spacestatus_irc.send_spaceapi()

    # SpaceStatus object
    spacestatus = SpaceStatus(settings.SPACESTATUS_FILE)
    spacestatus.state_changed_listenners.append(state_changed)

    get_logger().info("Initial state is {}".format(spacestatus.previous_state))

    # SpaceAPI object
    spaceapi = SpaceApi()

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

        elif command == 'open' or command == 'open_silent':
            different_state = not spacestatus.read_state()
            spacestatus.set_state(True)

            data = {
                'is_open': spacestatus.read_state(),
                'has_changed': different_state
            }
            rabbit.publish('spacestatus.answer', data)

            if command != 'open_silent' and different_state:
                rabbit.publish('spacestatus.broadcast', data)

        elif command == 'close' or command == 'close_silent':
            different_state = spacestatus.read_state()
            spacestatus.set_state(False)

            data = {
                'is_open': spacestatus.read_state(),
                'has_changed': different_state
            }
            rabbit.publish('spacestatus.answer', data)

            if command != 'close_silent' and different_state:
                rabbit.publish('spacestatus.broadcast', data)

    rabbit.listeners.append(query_closure)

    get_logger().info("Starting passive consumming...")
    rabbit.start_consuming()

    monitor_thread.join()
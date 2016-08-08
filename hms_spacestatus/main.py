import logging
from threading import Thread

import coloredlogs

from hms_base.client import Client
from hms_base.decorators import topic

from hms_spacestatus import settings
from hms_spacestatus.spacestatus import SpaceStatus, SpaceStatusIRC

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
        rabbit.publish("spacestatus_state_changed", {"new_value": newstate})
        spacestatus_irc.send_status()

    spacestatus = SpaceStatus(settings.SPACESTATUS_FILE)
    spacestatus.state_changed_listenners.append(state_changed)

    spacestatus_irc = SpaceStatusIRC(spacestatus, rabbit)

    monitor_thread = Thread(target=spacestatus.monitor)
    monitor_thread.setDaemon(True)

    get_logger().info("Starting file monitor thread...")
    monitor_thread.start()

    # Closure, cannot use @topic directly on method
    @topic('irc_command')
    def irc_closure(*args):
        spacestatus_irc.irc_command_listener(*args)

    rabbit.listeners.append(irc_closure)

    get_logger().info("Starting passive consumming...")
    rabbit.start_consuming()

    monitor_thread.join()
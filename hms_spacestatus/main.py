import logging

import coloredlogs

from hms_base.client import Client
from hms_spacestatus import settings
from hms_spacestatus.spacestatus import SpaceStatus

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

    spacestatus = SpaceStatus(settings.SPACESTATUS_DIRECTORY, settings.SPACESTATUS_FILE)
    spacestatus.state_changed_listenners.append(state_changed)

    spacestatus.monitor()
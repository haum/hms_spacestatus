# Configuration file for hms_spacestatus

# RabbitMQ

RABBIT_HOST = 'localhost'                   # Address of the server
RABBIT_EXCHANGE = 'haum'                    # Name of the direct exchanger

RABBIT_ROUTING_KEYS = ['irc_command']       # List of routing keys to listen to

# Spacestatus

SPACESTATUS_FILE = '/var/spacestatus/status'

# SpaceAPI

SPACEAPI_KEY = 'not_a_chance'

# Import production settings if existing

try:
    from hms_spacestatus.settings_prod import *
except ImportError:
    pass
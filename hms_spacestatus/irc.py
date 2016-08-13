import logging
import inspect


def get_logger():
    return logging.getLogger(__name__)


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
        self.irc_debug('Aide : !spacestatus pour voir si l’espace est ouvert')
        self.irc_debug('Aide : autres commandes !spacestatus [{}]'.format(commands_str))

    def on_open(self):
        self.on_open_silent()
        self.send_twaum()

    def on_open_silent(self):
        if self.spacestatus.read_state():
            self.irc_debug('Attention : l’espace est déjà ouvert !'.format())
        self.spacestatus.set_state(True)

    def on_close(self):
        self.on_close_silent()
        self.send_twaum()

    def on_close_silent(self):
        if not self.spacestatus.read_state():
            self.irc_debug('Attention : l’espace est déjà fermé !')
        self.spacestatus.set_state(False)

    def on_toggle(self):
        self.on_toggle_silent()
        self.send_twaum()

    def on_toggle_silent(self):
        self.spacestatus.set_state(not self.spacestatus.read_state())

    def send_status(self):
        msg = 'L’espace est fermé !'
        if self.spacestatus.read_state():
            msg = 'L’espace est ouvert !'

        self.irc_debug(msg)

    def send_twaum(self):
        if self.spacestatus.read_state():
            self.irc_debug('@tweet INFO : notre espace est tout ouvert, n’hésitez pas à passer si vous le voulez/pouvez ! haum.org')
        else:
            self.irc_debug('@tweet Fin de session ! Jetez un œil à notre agenda sur haum.org pour connaître les prochaines ou surveillez notre fil twitter.')
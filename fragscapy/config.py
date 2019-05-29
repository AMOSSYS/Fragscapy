"""Configuration parser and helper for fragscapy.

The `config module` is responsible for sanitizing, checking and parsing a
configfile provided by the user. It raises `ConfigError` and `ConfigWarning`
if wrong parameters are detected.
"""

import warnings
import json

class ConfigError(ValueError):
    """ Raises a configuration error about `key`. """
    def __init__(self, key):
        self.key = key
        super(ConfigError, self).__init__(
            "Error: Unable to read '{}'".format(key)
        )


class ConfigWarning(Warning):
    """ Warning during the configuration parsing. """
    pass


def config_warning(msg):
    """ Raises a warning about something, details in `msg`. """
    warnings.warn(
        "{}".format(msg),
        ConfigWarning
    )


def json_loadf(filename):
    """ Wrapper arround `json.load` to load directly from filename. """
    with open(filename) as f:
        return json.load(f)


class Config(object):
    """
    Configuration parser wrapper.
    Parse some given data to load the configuration to run fragscapy with.
    This is a wrapper that checks the correct format of the data and raises
    errors or warning when an anomaly is found. If everything is alright, it
    exposes the configuration as read-only data.

    >>> config = Config('config.json')
    >>> config.nfrules
    [{'host': 'www.lmddgtfy.com', 'port': 8080},
     {'host': 'www.lmddgtfy.com', 'port': 80}]
    >>> config.input
    ['tcp_sport 8080', 'echo "80 -> 8080"']
    >>> config.output
    ['tcp_dport 8080', 'echo "8080 -> 80"']

    :param data: The data to parse. It may be a file or a string depending on
        the parser used. If the default parser is used, it should be a
        filename.
    :param parser: The parser to use. It should respect the data types
        expected in the configuration. Default is `json_loadf`.
    """
    def __init__(self, data, parser=None):
        if parser is None:
            parser = json_loadf

        self.parser = parser
        self.data = data

        self._cmd = ""
        self._nfrules = list()
        self._input = list()
        self._output = list()

        self._parse()

    @property
    def cmd(self):
        """ The command to run for each test. """
        return self._cmd

    @property
    def nfrules(self):
        """ A list of key-words args to pass to NFQueueRule. """
        return self._nfrules

    @property
    def output(self):
        """ A list of args to pass to a modification for the output chain. """
        return self._output

    @property
    def input(self):
        """ A list of args to pass to a modification for the input chain. """
        return self._input

    def _parse(self):
        # Parse the data and interrupt if not readable
        try:
            user_data = self.parser(self.data)
        except Exception:
            raise ConfigError('.not_parsable')

        if not isinstance(user_data, dict):
            raise ConfigError('.not_dict')

        # Parse all the data coming from the user
        # and warn about unknown options
        for key, value in user_data.items():
            if key == 'cmd':
                self._parse_cmd(value)
            elif key == 'nfrules':
                self._parse_nfrules(value)
            elif key == 'input':
                self._parse_input(value)
            elif key == 'output':
                self._parse_output(value)
            else:
                config_warning(
                    "Unrecognized option found : '.{}'".format(key)
                )

        # Warning in the case of no nfrules which is weird but doable.
        if not self._nfrules:
            config_warning(
                "No Netfilter rules configured, which means no data will be "
                "intercepted. Be sure this is the intended behavior."
            )

    def _parse_cmd(self, user_cmd):
        if not isinstance(user_cmd, str):
            raise ConfigError('.cmd.not_str')
        if not user_cmd[0] == '/':
            config_warning(
                "The command is relative, you should consider using absolute "
                "commands for better stability."
            )
        self._cmd = user_cmd

    def _parse_nfrules(self, user_nfrules):
        if not isinstance(user_nfrules, list):
            raise ConfigError('.nfrules.not_list')

        self._nfrules = list()
        for i, user_nfrule in enumerate(user_nfrules):
            if not isinstance(user_nfrule, dict):
                raise ConfigError('.nfrules.{}.not_dict'.format(i))
            self._nfrules.append(user_nfrule)

    def _parse_input(self, user_input):
        if not isinstance(user_input, list):
            raise ConfigError('.input.not_list')

        self._input = list()
        for i, mod in enumerate(user_input):
            try:
                self._input.append(_parse_mod(mod))
            except ConfigError as e:
                raise ConfigError('.input.{}{}'.format(i, e.key))

    def _parse_output(self, user_output):
        if not isinstance(user_output, list):
            raise ConfigError('.output.not_list')

        self._output = list()
        for i, mod in enumerate(user_output):
            try:
                self._output.append(_parse_mod(mod))
            except ConfigError as e:
                raise ConfigError('.output.{}{}'.format(i, e.key))


def _parse_mod(mod):
    if not isinstance(mod, dict):
        raise ConfigError('.not_dict')

    mod_name = None
    mod_opts = list()

    for key, value in mod.items():
        if key == "mod_name":
            mod_name = value
        elif key == "mod_opts":
            if not isinstance(value, list):
                value = [value]
            mod_opts = value
        else:
            config_warning("Unrecognized option : {}".format(key))

    if mod_name is None:
        raise ConfigError('.missing_mod_name')

    return {
        "mod_name": mod_name,
        "mod_opts": mod_opts
    }

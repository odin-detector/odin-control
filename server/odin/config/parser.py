import sys
import argparse
from ConfigParser import SafeConfigParser
from functools import partial

import tornado.options

class ConfigError(Exception):
    pass

class ConfigParser(object):

    def __init__(self):

        self.allowed_options = {
            'server'  : {},
            'logging' : {}
        }

        self.arg_parser = argparse.ArgumentParser()
        self.file_parser = SafeConfigParser()

        self.define('config', default=None, metavar='FILE',
                    help='Specify a configuration file to parse')

    def define(self, name, default=None, type=None, help=None, metavar=None, multiple=False):

        self.allowed_options['server'][name] = ConfigOption(
            name, type=type, default=default, multiple=multiple)

        opt_switch = '--{}'.format(name)

        type = self.allowed_options['server'][name].type
        if multiple:
            type = partial(self.parse_multiple_arg, arg_type=type)

        default = None

        self.arg_parser.add_argument(opt_switch, type=type, default=default,
                                     help=help, metavar=metavar)

    def parse(self, args=None):

        if args == None:
            args = sys.argv

        tornado_opts = tornado.options.options._options
        self.allowed_options['logging'] = {}
        for opt in sorted(tornado_opts):
            if opt != 'help':
                opt_switch = '--{}'.format(tornado_opts[opt].name)
                self.arg_parser.add_argument(opt_switch, type=tornado_opts[opt].type,
                                             #default=tornado_opts[opt].default,
                                             help=tornado_opts[opt].help,
                                             metavar=tornado_opts[opt].metavar)
                self.allowed_options['logging'][tornado_opts[opt].name] = ConfigOption(
                    tornado_opts[opt].name, tornado_opts[opt].type, tornado_opts[opt].default
                )

        # Parse command-line arguments
        (arg_config, unused) = self.arg_parser.parse_known_args(args)

        file_config = {}
        for section in self.allowed_options:
            file_config[section] = {}

        if arg_config.config:
            self.file_parser = SafeConfigParser()

            try:
                with open(arg_config.config) as fp:
                    self.file_parser.readfp(fp)
            except Exception as e:
                raise ConfigError('Failed to parse configuration file: {}'.format(e))

            parser_get_map = {
                int   : self.file_parser.getint,
                float : self.file_parser.getfloat,
                bool  : self.file_parser.getboolean,
                str   : self.file_parser.get,
            }

            # Iterate over the allowed options from all sections and extract from the file configuration
            # if present

            for section in self.allowed_options:
                file_config[section] = {}
                if self.file_parser.has_section(section):
                    for option in self.allowed_options[section]:
                        if self.file_parser.has_option(section, option):

                            option_type = self.allowed_options[section][option].type

                            # Handle multiple values
                            if self.allowed_options[section][option].multiple:
                                option_str = self.file_parser.get(section, option)
                                value = self.parse_multiple_arg(option_str, arg_type=option_type)
                            else:
                                if option_type in parser_get_map:
                                    value = parser_get_map[option_type](section, option)
                                else:
                                    value = self.file_parser.get(section, option)
                        else:
                            value = None

                        file_config[section][option] = value

        # Now iterate over the allowed options and set attributes in the current parser for each, using,
        # in order of priority, the command-line argument, the config file or the default value.

        arg_config_vars = vars(arg_config)
        for section in self.allowed_options:
            for option in self.allowed_options[section]:
                option_val = None
                if option in file_config[section] and file_config[section][option] != None:
                    option_val = file_config[section][option]
                if option in arg_config_vars and arg_config_vars[option] != None:
                    option_val = vars(arg_config)[option]
                if option_val == None:
                    option_val = self.allowed_options[section][option].default

                setattr(self, option, option_val)

                # If this option is in the tornado options, update its value
                if option in tornado.options.options:
                    setattr(tornado.options.options, option, option_val)

        # Run the tornado parser callbacks to replicate the tornado parser behaviour
        tornado.options.options.run_parse_callbacks()

    def parse_multiple_arg(self, arg, arg_type=str, splitchar=','):

        try:
            return [arg_type(arg) for arg in arg.split(splitchar)]
        except ValueError:
            raise ConfigError('Multiple-valued argument contained element of incorrect type')


    def __contains__(self, item):

        for section in self.allowed_options:
            if item in self.allowed_options[section]:
                return True

        return False

    def __iter__(self):

        return (name for section in self.allowed_options for name in self.allowed_options[section])

class ConfigOption(object):

    """
    Simple container class to define a configuration option, its type and default
    value
    """

    def __init__(self, name, type=None, default=None, multiple=False):

        self.name = name
        self.type = type
        self.default = default
        self.multiple = multiple

        # Raise an error if type and defaultare inconsistent
        if self.type != None and self.default != None:
            if self.default.__class__ != self.type:
                raise ConfigError('Default value {} for option {} does not have correct type ({})'.format(
                    self.default, self.name, self.type
                ))

        # If absent, infer type from any default value given. Otherwise fall back
        # to string type to allow simple parsing from configuration input
        if self.type == None:
            if self.default != None:
                self.type = self.default.__class__
            else:
                self.type = str

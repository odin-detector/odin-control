import argparse
from ConfigParser import SafeConfigParser
import logging
import sys

import tornado.options

class ConfigError(Exception):
    pass

class ConfigParser(object):

    def __init__(self):

        self.allowed_options = {}
        self.allowed_options['server'] = {}

        self.arg_parser = argparse.ArgumentParser()

        self.define("config", default=None, metavar="FILE",
                    help="Specify a configuration file to parse")

    def define(self, name, default=None, type=None, help=None, metavar=None,
           multiple=False):

        self.allowed_options['server'][name] = ConfigOption(
            name, type=type, default=default)

        opt_switch = "--{}".format(name)
        type = self.allowed_options['server'][name].type
        default = None

        self.arg_parser.add_argument(opt_switch, type=type, default=default,
                                     help=help, metavar=metavar)

    def parse(self, args=None):

        if args == None:
            args = sys.argv

        tornado_opts = tornado.options.options._options
        self.allowed_options['logging'] = {}
        for opt in sorted(tornado_opts):
            if opt != "help":
                opt_switch = "--{}".format(tornado_opts[opt].name)
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
            file_parser = SafeConfigParser()
            file_parser.read(arg_config.config)

            parser_get_map = {
                int   : file_parser.getint,
                float : file_parser.getfloat,
                bool  : file_parser.getboolean,
                str   : file_parser.get,
            }

            for section in self.allowed_options:
                file_config[section] = {}
                if file_parser.has_section(section):
                    for option in self.allowed_options[section]:
                        if file_parser.has_option(section, option):
                            file_config[section][option] = file_parser.get(section, option)
                            option_type = self.allowed_options[section][option].type
                            if option_type in parser_get_map:
                                value = parser_get_map[option_type](section, option)
                            else:
                                value = file_parser.get(section, option)
                        else:
                            value = None

                        file_config[section][option] = value

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

                if option in tornado.options.options:
                    setattr(tornado.options.options, option, option_val)

        tornado.options.options.run_parse_callbacks()

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

    def __init__(self, name, type=None, default=None):

        self.name = name
        self.type = type
        self.default = default

        # Raise an error if type and defaultare inconsistent
        if self.type != None and self.default != None:
            if self.default.__class__ != self.type:
                raise ConfigError("Default value {} for option {} does not have correct type ({})".format(
                    self.default, self.name, self.type
                ))

        # If absent, infer type from any default value given. Otherwise fall back
        # to string type to allow simple parsing from configuration input
        if self.type == None:
            if self.default != None:
                self.type = self.default.__class__
            else:
                self.type = str

import argparse
from ConfigParser import SafeConfigParser
import logging
import sys

import tornado.options

class ConfigParser(object):

    def __init__(self):

        self.allowed_options = {}
        self.allowed_options['server'] = {}

        self.arg_parser = argparse.ArgumentParser()

        self.define("config", default=None, metavar="FILE",
                    help="Specify a configuration file to parse")


    def define(self, name, **kwargs):

        option_type = kwargs['type'] if 'type' in kwargs else None
        option_default = kwargs['default'] if 'default' in kwargs else None

        if option_type is None:
            if option_default != None:
                option_type = option_default.__class__
            else:
                option_type = str

        self.allowed_options['server'][name] = (option_type, option_default)

        opt_switch = "--{}".format(name)
        kwargs['type'] = option_type
        kwargs['default'] = None
        self.arg_parser.add_argument(opt_switch, **kwargs)

    def parse(self):

        tornado_opts = tornado.options.options._options
        self.allowed_options['logging'] = {}
        for opt in sorted(tornado_opts):
            if opt != "help":
                opt_switch = "--{}".format(tornado_opts[opt].name)
                self.arg_parser.add_argument(opt_switch, type=tornado_opts[opt].type,
                                             #default=tornado_opts[opt].default,
                                             help=tornado_opts[opt].help,
                                             metavar=tornado_opts[opt].metavar)
                self.allowed_options['logging'][tornado_opts[opt].name] = (
                    tornado_opts[opt].type, tornado_opts[opt].default
                )

        # Parse command-line arguments
        (arg_config, unused) = self.arg_parser.parse_known_args()

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
                            option_type = self.allowed_options[section][option][0]
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
                    source = "F"
                if option in arg_config_vars and arg_config_vars[option] != None:
                    option_val = vars(arg_config)[option]
                    source = "A"
                if option_val == None:
                    option_val = self.allowed_options[section][option][1]
                    source = "D"

                setattr(self, option, option_val)

                if option in tornado.options.options:
                    setattr(tornado.options.options, option, option_val)

        tornado.options.options.run_parse_callbacks()

class ConfigOption(object):

    def __init__(self, opt_name, opt_type=None, opt_default=None):

        self.name = opt_name
        self.type = opt_type
        self.default = opt_default

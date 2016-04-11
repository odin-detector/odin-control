import argparse
from ConfigParser import SafeConfigParser
import logging
import sys

import tornado.options

class ConfigParser(object):

    def __init__(self):

        self.option_type = {}

        self.arg_parser = argparse.ArgumentParser()

        self.define("config", default=None, metavar="FILE",
                    help="Specify a configuration file to parse")

        self.file_options = {

            'server' : {
                'debug_mode' : (bool, False),
                'http_addr'  : (str, '0.0.0.0'),
                'http_port'  : (int, 8888)
            },
        }

    def define(self, name, **kwargs):

        print "define: name={} kwargs={}".format(name, kwargs)
        # option_type = kwargs['type'] if 'type' in kwargs else None
        # option_default = kwargs['default'] if 'default' in kwargs else None
        #
        # if option_type is None:
        #     if option_default != None:
        #         option_type = option_default.__class__
        #     else:
        #         option_type = str
        #
        # kwargs[option_type] = type

        opt_switch = "--{}".format(name)
        self.arg_parser.add_argument(opt_switch, **kwargs)

    def parse(self):

        tornado_opts = tornado.options.options._options
        self.file_options['logging'] = {}
        for opt in sorted(tornado_opts):
            if opt != "help":
                print opt, tornado_opts[opt].name, tornado_opts[opt].type
                opt_switch = "--{}".format(tornado_opts[opt].name)
                self.arg_parser.add_argument(opt_switch, type=tornado_opts[opt].type,
                                             default=tornado_opts[opt].default,
                                             help=tornado_opts[opt].help,
                                             metavar=tornado_opts[opt].metavar)
                self.file_options['logging'][tornado_opts[opt].name] = (
                    tornado_opts[opt].type, tornado_opts[opt].default
                )

        print self.file_options
        print tornado_opts

        # Intercept the config command line option
        (arg_config, unused) = self.arg_parser.parse_known_args()

        print arg_config

        if arg_config.config:
            file_config = SafeConfigParser()
            file_config.read(arg_config.config)

            allowed_sections = ['server', 'logging']

            for section in allowed_sections:
                if file_config.has_section(section):
                    for option in file_config.options(section):
                        print section, option
                        if option in tornado.options.options:
                            opt_present = "yes"
                            opt_type = "???" # self.option_type[option]
                        else:
                            opt_present = "no"
                            opt_type = str
                        print "{} : {} present {} type {}".format(option, file_config.get(section, option),
                                                                  opt_present, opt_type)
                        #setattr(tornado.options.options, option, value)

        #tornado.options.parse_command_line()

    # def __getattr__(self, name):
    #
    #     return getattr(tornado.options.options, name)
    #
    # def __setattr__(self, name, value):
    #
    #     return setattr(tornado.options.options, name, value)
    #
    # def __contains__(self, name):
    #
    #     return name in tornado.options.options

    def items(self):

        return tornado.options.options.items()
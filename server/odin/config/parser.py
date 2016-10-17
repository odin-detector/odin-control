"""odin.config.parser - configuration parsing for the ODIN server.

Tim Nicholls, STFC Application Engineering Group
"""
from odin._version import get_versions

import sys
from argparse import ArgumentParser
from functools import partial
import tornado.options

if sys.version_info[0] == 3:                  # pragma: no cover
    from configparser import SafeConfigParser
else:                                         # pragma: no cover
    from ConfigParser import SafeConfigParser


class ConfigError(Exception):
    """ConfigParser exception class.

    A trivial exception class for signalling configuration parsing errors
    """

    pass


class ConfigParser(object):
    """Parses configuration options from the command-line and from a file.

    Provides parsing of program configuration options from both command-line arguments and
    from an INI-style file. This class is designed to integrate and replace the default Tornado
    options parser, which has limitations in prioritising options from multiple sources. Parsed
    options are set as attributes of the object, allowing the calling program to easily resolve
    them.

    Options specified at the command-line take priority over the value present in any configuration
    file specified. Any options already defined by Tornado packages at parse time are integrated
    into this parser and can be specified in the [tornado] section of the configuration file.
    Similarly, options defined by this parser are specified in the [server] section.

    API adapters are treated as a special case of file-only configuration. If the adapters config
    option is defined (either in command-line args or in a configuration file) then the
    resolve_adapters() method can be used to extract adapter-specific options from a section named
    [adapter.<adapter_name>].
    """

    def __init__(self, has_adapters=True):
        """Initialise the configuration parser.

        :param has_adapters: if True, automatically define an --adapters option in the parser
        """
        # Initialise allowed options sections
        self.allowed_options = {
            'server':  {},
            'tornado': {},
        }

        # Create CLI argument and file configuration parsers. This class uses the python
        # argparse module for command-line arguments rather than the Tornado options implementation.
        self.arg_parser = ArgumentParser()
        self.file_parser = SafeConfigParser()
        self.file_parsed = False

        # Define a --version option to return the ODIN server version
        self.define('version', option_type=bool, default=False, action='store_true',
                    option_help='Show the server version information and exit',
                    callback=self._version_callback)

        # Define a --config option to specify configuration file to parse.
        self.define('config', default=None, metavar='FILE',
                    option_help='Specify a configuration file to parse')

        # If has_adapters argument is True, define a --adapters config option
        if has_adapters:
            self.define('adapters', option_type=str, multiple=True,
                        option_help='Comma-separated list of API adapters to load')

    def define(self, name, default=None, option_type=None, option_help=None, metavar=None,
               multiple=False, action='store', callback=None):
        """Define an option to be parsed from the command-line and/or a configuration file.

        This method replicates the functionality of the tornado options define(), allowing
        options to be defined for parsing. Named options can be given a default value, a type,
        which can either be given explicitly or inferred from the default value if given,
        ``help`` and ``metavar`` values for display in command-line help, and a ``multiple``
        flag to allow comma-delimited multiple values to be specified.

        :param name: name of the option
        :param default: default value for the option
        :param option_type: type of the option (e.g. int, bool, str)
        :param option_help: help text to be displayed for the option
        :param metavar: a name for the option to be used in help text
        :param multiple: defines if the option accepts multiple, comma-delimited values
        :param action: ArgumentParser-like action to be taken on parsing option
        :param callback: callback to run whenever a value for the option is set at parse time
        :return: None
        """
        # Add the option to allowed_options
        self.allowed_options['server'][name] = ConfigOption(
            name, option_type=option_type, default=default, multiple=multiple, callback=callback)

        # Format the CLI option switch
        opt_switch = '--{}'.format(name)

        # Resolve the option type, which may have been inferred from the default value
        # if not sepcified. If multiple values are allowed, create a type-specific
        # parsing partial function to allow comma-separated values to be resolved and
        # cast to appropriate type
        option_type = self.allowed_options['server'][name].option_type
        if multiple:
            option_type = partial(_parse_multiple_arg, arg_type=option_type)

        # Clear the default flag so that CLI arguments don't automatically have the
        # default value assigned by the parser, clobbering any value in the file. The
        # default value specified by this call is resolved at parse time if necessary.
        default = None

        # Build the kwargs for the add_argument call for the parser. If a boolean
        # flag action has been specified, i.e. store_true or store_false, don't add the
        # type and metavar keyword arguments as their presence causes an exception to be
        # thrown
        add_kwargs = {
            'action': action, 'default': default,
            'help': option_help,
        }
        if action != 'store_true' and action != 'store_false':
            add_kwargs['type'] = option_type
            add_kwargs['metavar'] = metavar

        # Add the option as an argument to the CLI parser
        self.arg_parser.add_argument(opt_switch, **add_kwargs)

        # Set this option as an attribute in the current instance but with an undefined
        # value until parsing occurs. The allows the parser.<option> syntax to be used
        # without error throughout the lifetime of the instance
        setattr(self, name, None)

    def parse(self, args=None):
        """Parse command-line and file configuration options.

        This method parses command-line and file (if specified a ``--config`` argument)
        configuration options. The parser will parse command-line options from the
        program invocation arguments or, if specified in the ``args`` parameter, from
        a string with the appropriate format.

        This method resolves any options already loaded into the global tornado options
        instance and parses them from the command-line or the [tornado] section of a
        configuration file. Those options are loaded back into the tornado options
        instance on completion of parsing, and the the tornado parser callbacks invoked
        to replicate the desired behaviour.

        :param args: optional string containing arguments to parse
        :return: None
        """
        # If args not specified, use the program command-line argv string
        if args is None:
            args = sys.argv

        # Load existing tornado options into the parser
        self._load_tornado_options()

        # Parse command-line arguments
        (arg_config, _) = self.arg_parser.parse_known_args(args)

        # Parse file configuration options
        file_config = self._parse_file_config(arg_config.config)

        # Now iterate over the allowed options and set attributes in the current parser for each,
        # using, in order of priority, the command-line argument, the config file or the default
        # value.
        arg_config_vars = vars(arg_config)
        for section in self.allowed_options:
            for option in self.allowed_options[section]:
                option_val = None
                if option in file_config[section] and file_config[section][option] is not None:
                    option_val = file_config[section][option]
                if option in arg_config_vars and arg_config_vars[option] is not None:
                    option_val = vars(arg_config)[option]
                if option_val is None:
                    option_val = self.allowed_options[section][option].default

                # Set option as attribute in this instance
                setattr(self, option, option_val)

                # If this option is in the tornado options, update its value
                if option in tornado.options.options:
                    setattr(tornado.options.options, option, option_val)

                # If this option has a callback, call it
                if self.allowed_options[section][option].callback is not None:
                    self.allowed_options[section][option].callback(option_val)

        # Run the tornado parser callbacks to replicate the tornado parser behaviour
        tornado.options.options.run_parse_callbacks()

    def _parse_file_config(self, config_file):
        """Parse a configuration file (INTERNAL METHOD).

        :param config_file: name of configuration file to parse
        :return: container of resolved file configuration options
        """
        # Initialise a container for resolved file configuration options
        file_config = {}
        for section in self.allowed_options:
            file_config[section] = {}

        # If a --config options was parsed, attempt to parse the specified file
        if config_file:

            try:
                with open(config_file) as config_fp:
                    self.file_parser.readfp(config_fp)
            except Exception as e:
                raise ConfigError('Failed to parse configuration file: {}'.format(e))

            self.file_parsed = True

            # Define a mapping between option types and the file parser getter methods
            parser_get_map = {
                int: self.file_parser.getint,
                float: self.file_parser.getfloat,
                bool: self.file_parser.getboolean,
                str: self.file_parser.get,
            }

            # Iterate over the allowed options from all sections and extract from the file
            # configuration if present
            for section in self.allowed_options:
                file_config[section] = {}
                if self.file_parser.has_section(section):
                    for option in self.allowed_options[section]:
                        if self.file_parser.has_option(section, option):

                            option_type = self.allowed_options[section][option].option_type

                            # Handle multiple values
                            if self.allowed_options[section][option].multiple:
                                option_str = self.file_parser.get(section, option)
                                value = _parse_multiple_arg(option_str, arg_type=option_type)
                            else:
                                if option_type in parser_get_map:
                                    value = parser_get_map[option_type](section, option)
                                else:
                                    value = self.file_parser.get(section, option)
                        else:
                            value = None

                        file_config[section][option] = value

        return file_config

    def _load_tornado_options(self):
        """Load tornado options into the parser (INTERNAL METHOD)."""
        tornado_opts = tornado.options.options._options
        self.allowed_options['tornado'] = {}
        for opt in sorted(tornado_opts):
            if opt != 'help':
                opt_switch = '--{}'.format(tornado_opts[opt].name)
                self.arg_parser.add_argument(opt_switch, type=tornado_opts[opt].type,
                                             help=tornado_opts[opt].help,
                                             metavar=tornado_opts[opt].metavar)
                self.allowed_options['tornado'][tornado_opts[opt].name] = ConfigOption(
                    tornado_opts[opt].name, tornado_opts[opt].type, tornado_opts[opt].default
                )

    def _version_callback(self, value):
        """Print the odin server version information and exit."""
        if value:
            print("odin server {}".format(get_versions()['version']))
            sys.exit(0)

    def resolve_adapters(self, adapter_list=None):
        """Resolve any adapter sections present in the configuration file.

        This method resovles adapter sections preent in the configuration file into a usable
        list of adapters to be loaded and configured by the server.

        :param adapter_list: a list of adapter names to resolve. If not set, the
            parsers adapters attribute will be substituted

        :return: dict of AdapterConfig objects from the configuration file
        """
        resolved_adapters = {}

        # If no adapter names to resolve were specified, determine if any were given
        # in the command line or file configuration.
        if adapter_list is None:
            try:
                adapter_list = getattr(self, 'adapters')
            except AttributeError:
                raise ConfigError('Configuration parser has no adapter option set')
            if adapter_list is None:
                raise ConfigError("No adapters specified in configuration")

        # If a configuration file wasn't parsed, it won't be possible to resolve adapter-specific
        # sections so raise an error
        if not self.file_parsed:
            raise ConfigError('No configuration file parsed, unable to resolve adapters')

        # Loop over the specified adapters
        for adapter in adapter_list:

            # Build the section name in the config file as [adapter.<adapter_name>]
            section_name = 'adapter.{}'.format(adapter)

            # Check section is present otherwise raise an error
            if not self.file_parser.has_section(section_name):
                raise ConfigError(
                    'Configuration file has no section for adapter {}'.format(adapter)
                )

            # Check that the compulsory module option is present in the adapter section
            if not self.file_parser.has_option(section_name, 'module'):
                raise ConfigError(
                    'Configuration file has no module parameter for adapter {}'.format(adapter)
                )

            # Create a new adapter configuration object and add it to the returned dictionary
            module = self.file_parser.get(section_name, 'module')
            resolved_adapters[adapter] = AdapterConfig(adapter, module)

            # Extract any other adapter-specific options and set them as attributes in the config
            # object
            for (name, value) in self.file_parser.items(section_name):
                if name == 'module':
                    continue
                resolved_adapters[adapter].set(name, value)

        return resolved_adapters

    def __contains__(self, item):
        """Containment check operator - allows ``in`` to check for presence of option.

        :param item: item to check for presence
        """
        return hasattr(self, item)

    def __iter__(self):
        """Return an iterator object over the options specified in the current instance."""
        return (name for section in self.allowed_options for name in self.allowed_options[section])


def _parse_multiple_arg(arg, arg_type=str, splitchar=','):
    """Parse comma-delimited multiple arguments into a typed list.

    This function splits comma-delimited multiple-valued options from arguments or configuration
    files. The argument string is split on the specified character (comma by default), each element
    is cast to the appropriate type and is returned in a list.

    :param arg: argument/option string to be resolved. e.g ``1,2,3,4``
    :param arg_type: argument type to resolve, e.g. int, float, bool or str
    :param splitchar: character to split string on, comma by default
    :return: list of resolved, type-cast values from the argument string
    """
    try:
        # Split the string, strip off any whitespace and return as a list
        return [arg_type(elem.strip()) for elem in arg.split(splitchar)]
    except ValueError:
        raise ConfigError('Multiple-valued argument contained element of incorrect type')


class ConfigOption(object):
    """A configuration option container class.

    A simple container class used internally by ConfigParser to define a configuration option,
    its type, default value and whether it has multiple values
    """

    def __init__(self, name, option_type=None, default=None, multiple=False, callback=None):
        """Initialise the ConfigOption object.

        :param name: name of the option
        :param option_type: type of the option (e.g. int, bool, str, ...)
        :param default:  default value for the option
        :param multiple: flag indicating multiple-valued option
        :param callback: callback to be called whenever option has a value set at parse time
        """
        self.name = name
        self.option_type = option_type
        self.default = default
        self.multiple = multiple
        self.callback = callback

        # Raise an error if specified option_type and default are inconsistent
        if self.option_type is not None and self.default is not None:
            if self.default.__class__ != self.option_type:
                raise ConfigError(
                    'Default value {} for option {} does not have correct type ({})'.format(
                        self.default, self.name, self.option_type
                    )
                )

        # If absent, infer option_type from any default value given. Otherwise fall back
        # to string option_type to allow simple parsing from configuration input
        if self.option_type is None:
            if self.default is not None:
                self.option_type = self.default.__class__
            else:
                self.option_type = str


class AdapterConfig(object):
    """An adapter configuration container class.

    A simple container class used by ConfigParser to define the options for an API adapter. This
    class contains at least the name and module path for the adapter, plus any other options can
    be set as attributes using the set() method
    """

    def __init__(self, name, module):
        """Initialise the AdapterConfig object.

        :param name: name of the adapter
        :param module: module path for the adapter
        """
        self.name = name
        self.module = module
        self._options = {}

    def set(self, option, value):
        """Set an option for the adapter configuration object.

        :param option: name of the option
        :param value: value of the option
        :return: None
        """
        self._options[option] = value

    def __contains__(self, option):
        """Containment check operator - allows ``in`` to check for presence of option.

        :param option: name of option to check for
        :return: bool True or False indicating presence of option
        """
        return option in self._options

    def __getattr__(self, option):
        """Attribute getter allowing adapter options to be accessed by object.option syntax.

        :param option: name option to get
        :return: value of the requested option
        :raises: AttributeError for unrecognised option
        """
        if option not in self._options:
            raise AttributeError('Unrecognised option {}'.format(option))

        return self._options[option]

    def options(self):
        """Return a dictionary of the options set in the object.

        :return: dictionary of options
        """
        return self._options

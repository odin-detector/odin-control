import sys
import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

import pytest

import tornado.options

if sys.version_info[0] == 3:  # pragma: no cover
    from io import StringIO
    from configparser import ConfigParser as NativeConfigParser
else:                         # pragma: no cover
    from StringIO import StringIO
    from ConfigParser import SafeConfigParser as NativeConfigParser

from odin.config.parser import ConfigParser, ConfigOption, ConfigError, AdapterConfig, _parse_multiple_arg


class TestConfigOption():
    """Class to test configuration option behaviour."""

    def test_simple_option(self):
        """Test that a simple config option has the correct fields."""
        opt_name = 'simple'
        opt_type = bool
        opt_default = True

        opt = ConfigOption(opt_name, opt_type, opt_default)

        assert opt.name == opt_name
        assert opt.option_type == opt_type
        assert opt.default == opt_default

    def test_option_with_only_name(self):
        """Test that a config option with only a name defined has the correct fields."""
        opt_name = 'simple'

        opt = ConfigOption(opt_name)

        assert opt.name == opt_name
        assert opt.option_type == str
        assert opt.default == None

    def test_option_with_default(self):
        """Test that a config option with a default value has the correct fields."""
        opt_name = 'simple'
        opt_default = 'easy, huh?'

        opt = ConfigOption(opt_name, default=opt_default)

        assert opt.name == opt_name
        assert opt.default == opt_default
        assert opt.option_type == opt_default.__class__

    def test_option_with_wrong_default_type(self):
        """Test that a config option with an incorrectr type raises an exception."""
        opt_name = 'simple'
        opt_default = 1234
        opt_type = bool

        with pytest.raises(ConfigError) as excinfo:
            _ = ConfigOption(opt_name, option_type=opt_type, default=opt_default)

        assert "Default value {} for option {} does not have correct type ({})".format(
                 opt_default, opt_name, opt_type
             ) in str(excinfo.value)

class TestAdapterConfig():
    """Class to test adapter configuration objects."""

    def test_basic_adapter_config(self):
        """Test that a basic adapter config object has the correct fields."""
        name = 'test_adapter'
        module = 'path.to.module'

        ac = AdapterConfig(name, module)

        assert ac.name == name
        assert ac.module == module

    def test_adapter_config_set(self):
        """Test that an adapter config object with options is populated correctly."""
        ac = AdapterConfig('test_adapter', 'path.to.module')

        option1_name = 'option1'
        option1_val  = 'value1'

        option2_name = 'option2'
        option2_val  = 'value2'

        ac.set(option1_name, option1_val)
        ac.set(option2_name, option2_val)

        assert option1_name in ac
        assert option2_name in ac

        assert ac.option1 == option1_val
        assert ac.option2 == option2_val

        with pytest.raises(AttributeError) as excinfo:
            _ = ac.option3
        assert "Unrecognised option option3" in str(excinfo.value)

        ac_options = ac.options()

        assert type(ac_options) is dict
        assert len(ac_options) == 2
        assert option1_name in ac_options
        assert option2_name in ac_options


@pytest.fixture()
def test_config_parser():
    """Simple test fixture that creates a configuraiton parser."""
    cp = ConfigParser()
    yield cp

class AdapterTestConfig():
    """Container for the configuration needed to test Adapter configuration."""
    def __init__(self):
        self.adapters = ['dummy', 'dummy2']
        self.options = {
        'dummy' : {
            'module'     : 'odin.adapters.dummy.DummyAdapter',
            'test_param' : '13.46',
        },
        'dummy2' : {
            'module'     : 'odin.adapters.dummy.DummyAdapter',
            'other_param' : 'wibble',
        },
    }


@pytest.fixture(scope="class")
def adapter_test_config():
    """Simple test fixture to generate a test configuration container."""
    return AdapterTestConfig()

@pytest.fixture(scope="class")
def test_config_file(adapter_test_config):
    """Test fixture to generate a valid configuration file."""
    test_config_server_options = {
        'debug_mode' : '1',
        'http_port'  : '8888',
        'http_addr'  : '0.0.0.0',
        'adapters'   : ','.join(adapter_test_config.adapters),
        'wrapped'    : 'wrapped_str'
    }

    # Create a test config in a temporary file for use in tests
    test_config_file = NamedTemporaryFile(mode='w+')
    test_config = NativeConfigParser()

    test_config.add_section('server')
    for option in test_config_server_options:
        test_config.set('server', option,
            test_config_server_options[option])

    test_config.add_section('tornado')
    test_config.set('tornado', 'logging', 'debug')

    for adapter in adapter_test_config.options:

        section_name = 'adapter.{}'.format(adapter)
        test_config.add_section(section_name)

        for option in adapter_test_config.options[adapter]:
            test_config.set(section_name, option,
                    adapter_test_config.options[adapter][option])

    test_config.write(test_config_file)
    test_config_file.file.flush()

    yield test_config_file

    test_config_file.close()

@pytest.fixture(scope="class")
def bad_config_file():
    """Test fixutre to generate a bad configuration file with the wrong syntax."""
    bad_config_file = NamedTemporaryFile(mode='w+')
    bad_config_file.write('amo, amas, amat, amamum, amatis, amant\n')
    bad_config_file.file.flush()

    yield bad_config_file

    bad_config_file.close()

@pytest.fixture(scope="class")
def missing_adapter_config_file():
    """Test fixutre to generate a configuration file a missing adapter."""
    missing_adapter_file = NamedTemporaryFile(mode='w+')
    missing_adapter_config = NativeConfigParser()

    missing_adapter_config.add_section('server')
    missing_adapter_config.set('server', 'adapters', 'missing')
    missing_adapter_config.set('server', 'debug_mode', '1')

    missing_adapter_config.add_section('adapter.missing')
    missing_adapter_config.set('adapter.missing', 'dummy', 'nothing')

    missing_adapter_config.write(missing_adapter_file)
    missing_adapter_file.file.flush()

    yield missing_adapter_file

    missing_adapter_file.close()

class TestConfigParser():
    """Class to test the ODIN configuration parser."""

    def test_default_parser(self, test_config_parser):
        """Test that a default config parser has at least a config option."""
        assert 'config' in test_config_parser

    def test_supplied_args(self, test_config_parser):
        """Test that args supplied to a parser from e.g. the command line are parsed correctly."""
        port = 8989
        addr = '127.0.0.1'
        default_opt_val = False

        test_config_parser.define('http_addr', default='0.0.0.0',
            option_help='Set HTTP server address')
        test_config_parser.define('http_port', default=8888,
            option_help='Set HTTP server port')
        test_config_parser.define('default_opt', default=default_opt_val,
            option_help='Default option')

        test_args=['prog_name', '--http_port', str(port), '--http_addr', str(addr)]

        test_config_parser.parse(test_args)

        assert test_config_parser.http_port == port
        assert test_config_parser.http_addr == addr
        assert test_config_parser.default_opt == default_opt_val

    def test_imports_tornado_opts(self, test_config_parser):
        """Test that the parser correctly imports tornado options."""
        test_args=['prog_name']

        test_config_parser.parse(test_args)

        tornado_opts = tornado.options.options._options

        for opt in tornado_opts:
            if tornado_opts[opt].name != 'help':
                assert tornado_opts[opt].name in test_config_parser

    def test_version_arg_handling(self, test_config_parser, capsys):
        """Test that requesting the version returns a version and exits."""
        test_args = ['prog_name', '--version']

        with pytest.raises(SystemExit) as excinfo:
            test_config_parser.parse(test_args)

        assert excinfo.value.code == 0

        captured = capsys.readouterr()
        assert "odin control" in captured.out

    def test_ignores_undefined_arg(self, test_config_parser):
        """Test that undefined arguments supplied to the config parser are ignored."""
        test_args = ['prog_name', '--ignored', '1234']

        test_config_parser.parse(test_args)

        assert 'ignored' not in test_config_parser

    def test_parser_iterator(self, test_config_parser):
        """Test that the parser returns an iterator."""
        test_config_parser.parse()

        parser_opts = [opt for opt in test_config_parser]
        assert len(parser_opts) > 0

    def test_mismatched_arg_type(self, test_config_parser, capsys):
        """Test that an invalid argument type returns an error and exits."""
        test_config_parser.define('intopt', default=1234, option_type=int,
            option_help='This is an integer option')
        test_args = ['prog_name', '--intopt', 'wibble']

        with pytest.raises(SystemExit) as excinfo:
            test_config_parser.parse(test_args)

        assert excinfo.value.code == 2

        captured = capsys.readouterr()
        assert 'invalid int value' in captured.err

    def test_parse_file(self, test_config_parser, test_config_file):
        """Test that the parser correctly parses a file."""
        test_config_parser.define('debug_mode', default=False, option_type=bool,
            option_help='Enable tornado debug mode')

        test_args = ['prog_name', '--config', test_config_file.name]

        test_config_parser.parse(test_args)

        assert test_config_parser.debug_mode

    def test_parse_missing_file(self, test_config_parser):
        """Test that attempting to parse a non-existing config file raises an error."""
        config_file = 'missing.cfg'
        config_path = os.path.join(os.path.dirname(__file__), config_file)

        test_args = ['prog_name', '--config', config_path]

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.parse(test_args)

        assert "Failed to parse configuration file: [Errno 2] No such file or directory" \
            in str(excinfo.value)

    def test_parse_bad_file(self, test_config_parser, bad_config_file):
        """Test that a bad config file without sections raises an error."""

        test_args = ['prog_name', '--config', bad_config_file.name]

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.parse(test_args)

        assert 'Failed to parse configuration file: File contains no section headers' \
            in str(excinfo.value)

    def test_multiple_arg_parse(self):
        """Test that parsing multiple comma-separated arguments to a configuration works."""
        multiarg_list = ['dummy1', 'dummy2', 'dummy3']
        multiarg_str = ','.join(multiarg_list)

        split_args = _parse_multiple_arg(multiarg_str, arg_type=str, splitchar=',')

        assert len(multiarg_list) == len(split_args)
        for (elem_in, elem_out) in zip(multiarg_list, split_args):
            assert elem_in == elem_out

    def test_mismatched_multiple_arg_parse(self):
        """Test that mismatched types in multi-args raises an error."""
        multiarg_list = ['123', 'dummy2', 'dummy3']
        multiarg_str = ','.join(multiarg_list)

        with pytest.raises(ConfigError) as excinfo:
            _parse_multiple_arg(multiarg_str, arg_type=int, splitchar=',')

        assert 'Multiple-valued argument contained element of incorrect type' in str(excinfo.value)

    def test_multiple_option(self, test_config_parser):
        """Test that multiple options are parsed correctly."""
        test_config_parser.define('intvals', option_type=int, multiple=True,
            option_help='Integer list')

        adapter_list = ['dummy', 'dummy2 ', 'dummy3']
        adapter_str = ','.join(adapter_list)

        int_list = ['123', '456']
        int_str = ','.join(int_list)

        test_args = ['prog_name', '--adapters', adapter_str, '--intvals', int_str]

        test_config_parser.parse(test_args)

        assert 'adapters' in test_config_parser
        assert type(test_config_parser.adapters) == type(adapter_list)
        assert len(test_config_parser.adapters) == len(adapter_list)

        assert 'intvals' in test_config_parser
        assert type(test_config_parser.intvals) == type(int_list)
        assert len(test_config_parser.intvals) == len(int_list)

    def test_bad_multiple_option(self, test_config_parser):
        """Test that mismatched multiple-valued optins are handled by the parser correctly."""
        test_config_parser.define('intvals', option_type=int, multiple=True,
            option_help='Integer list')

        bad_list = ['123', '456', 'oops']
        bad_str = '.'.join(bad_list)

        test_args = ['prog_name', '--intvals', bad_str]

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.parse(test_args)

        assert "Multiple-valued argument contained element of incorrect type" in str(excinfo.value)

    def test_multiple_option_in_file(self, test_config_parser, test_config_file):
        """Test tha multiple-valued options in a file are parsed correctly."""
        test_args = ['prog_name', '--config', test_config_file.name]

        test_config_parser.parse(test_args)

        assert 'adapters' in test_config_parser
        assert type(test_config_parser.adapters) is list

    def test_option_type_not_in_map(self, test_config_parser, test_config_file):
        """ Test that a custom option type not in the default map is handled correctly."""
        class StrWrapper(str):
            pass

        test_config_parser.define('wrapped', option_type=StrWrapper, option_help='Wrapped String')

        test_args = ['prog_name', '--config', test_config_file.name]

        test_config_parser.parse(test_args)
        assert test_config_parser.wrapped == 'wrapped_str'

    def test_parser_with_no_config_for_adapters(self, test_config_parser):
        """Test that an empty configuration with no adapters raises an error on resolving."""
        test_config_parser.parse()

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.resolve_adapters(adapter_list=['dummy', 'dummy2'])

        assert "No configuration file parsed, unable to resolve adapters" in str(excinfo.value)

    def test_parser_with_adapters_disabled(self):
        """Test that a parser with adapters disabled raises an error on resolving."""
        noadapter_cp = ConfigParser(has_adapters=False)
        noadapter_cp.parse()

        with pytest.raises(ConfigError) as excinfo:
            noadapter_cp.resolve_adapters()

        assert "Configuration parser has no adapter option set" in str(excinfo.value)

    def test_parser_no_config_file_for_adapters(self, test_config_parser):
        """Test that a parser and with adapter specified but no adapter section raises an error."""
        test_args = ['prog_name', '--adapters', 'dummy']
        test_config_parser.parse(test_args)

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.resolve_adapters()

        assert "No configuration file parsed, unable to resolve adapters" in str(excinfo.value)

    def test_parser_config_missing_adapter_module(
            self, test_config_parser, missing_adapter_config_file
        ):
        """Test that parsing a config file with missing adapters raises an error on resolving."""
        test_args = ['prog_name', '--config', missing_adapter_config_file.name]
        test_config_parser.parse(test_args)

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.resolve_adapters()

        assert "Configuration file has no module parameter for adapter missing" \
            in str(excinfo.value)

    def test_resolve_adapters(self, test_config_parser, test_config_file, adapter_test_config):
        """Test that a fully specified adapter configuration parses correctly."""
        test_args = ['prog_name', '--config', test_config_file.name]

        test_config_parser.parse(test_args)

        assert test_config_parser.adapters == adapter_test_config.adapters

        with pytest.raises(ConfigError) as excinfo:
            test_config_parser.resolve_adapters(adapter_list=['dummy', 'missing'])

        assert 'Configuration file has no section for adapter ' in str(excinfo.value)

        adapters = test_config_parser.resolve_adapters()

        for adapter in adapters:
            assert type(adapters[adapter]) is AdapterConfig

            for option in adapter_test_config.options[adapter]:
                assert adapter_test_config.options[adapter][option] == \
                    getattr(adapters[adapter], option)
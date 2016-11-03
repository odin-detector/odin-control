from nose.tools import *
import tornado.options

import sys
import os
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

if sys.version_info[0] == 3:  # pragma: no cover
    from io import StringIO
    from configparser import SafeConfigParser
else:                         # pragma: no cover
    from StringIO import StringIO
    from ConfigParser import SafeConfigParser

from odin.config.parser import ConfigParser, ConfigOption, ConfigError, AdapterConfig, _parse_multiple_arg


class TestConfigOption():


    def test_simple_option(self):

        opt_name = 'simple'
        opt_type = bool
        opt_default = True

        opt = ConfigOption(opt_name, opt_type, opt_default)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.option_type, opt_type)
        assert_equal(opt.default, opt_default)

    def test_option_with_only_name(self):

        opt_name = 'simple'

        opt = ConfigOption(opt_name)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.option_type, str)
        assert_equal(opt.default, None)

    def test_option_with_default(self):

        opt_name = 'simple'
        opt_default = 'easy, huh?'

        opt = ConfigOption(opt_name, default=opt_default)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.default, opt_default)
        assert_equal(opt.option_type, opt_default.__class__)

    def test_option_with_wrong_default_type(self):

        opt_name = 'simple'
        opt_default = 1234
        opt_type = bool

        with assert_raises(ConfigError) as cm:
            opt = ConfigOption(opt_name, option_type=opt_type, default=opt_default)
        assert_equal(str(cm.exception),
             'Default value {} for option {} does not have correct type ({})'.format(
                 opt_default, opt_name, opt_type
             ))

class TestAdapterConfig():

    def test_basic_adapter_config(self):

        name = 'test_adapter'
        module = 'path.to.module'

        ac = AdapterConfig(name, module)

        assert_equal(ac.name, name)
        assert_equal(ac.module, module)

    def test_adapter_config_set(self):

        ac = AdapterConfig('test_adapter', 'path.to.module')

        option1_name = 'option1'
        option1_val  = 'value1'

        option2_name = 'option2'
        option2_val  = 'value2'

        ac.set(option1_name, option1_val)
        ac.set(option2_name, option2_val)

        assert_true(option1_name in ac)
        assert_true(option2_name in ac)

        assert_equal(ac.option1, option1_val)
        assert_equal(ac.option2, option2_val)

        with assert_raises_regexp(AttributeError, 'Unrecognised option option3'):
            option3 = ac.option3

        ac_options = ac.options()
        assert_true(type(ac_options) is dict)
        assert_equal(len(ac_options), 2)
        assert_true(option1_name in ac_options)
        assert_true(option2_name in ac_options)

class TestConfigParser():

    @contextmanager
    def capture_sys_output(self):
        capture_out, capture_err = StringIO(), StringIO()
        current_out, current_err = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = capture_out, capture_err
            yield capture_out, capture_err
        finally:
            sys.stdout, sys.stderr = current_out, current_err

    @classmethod
    def setup_class(cls):

        cls.test_config_adapter_list = ['dummy', 'dummy2']
        cls.test_config_adapter_options = {
            'dummy' : {
                'module'     : 'odin.adapters.dummy.DummyAdapter',
                'test_param' : '13.46',
            },
            'dummy2' : {
                'module'     : 'odin.adapters.dummy.DummyAdapter',
                'other_param' : 'wibble',
            },
        }

        cls.test_config_server_options = {
            'debug_mode' : '1',
            'http_port'  : '8888',
            'http_addr'  : '0.0.0.0',
            'adapters'   : ','.join(cls.test_config_adapter_list),
            'wrapped'    : 'wrapped_str'
        }

        # Create a test config in a temporary file for use in tests
        cls.test_config_file = NamedTemporaryFile(mode='w+')
        cls.test_config = SafeConfigParser()

        cls.test_config.add_section('server')
        for option in cls.test_config_server_options:
            cls.test_config.set('server', option,
                cls.test_config_server_options[option])

        cls.test_config.add_section('tornado')
        cls.test_config.set('tornado', 'logging', 'debug')

        for adapter in cls.test_config_adapter_options:

            section_name = 'adapter.{}'.format(adapter)
            cls.test_config.add_section(section_name)

            for option in cls.test_config_adapter_options[adapter]:
                cls.test_config.set(section_name, option,
                        cls.test_config_adapter_options[adapter][option])


        cls.test_config.write(cls.test_config_file)
        cls.test_config_file.file.flush()

        # Create a bad configuration with the wrong syntax for use in tests
        cls.bad_config_file = NamedTemporaryFile(mode='w+')
        cls.bad_config_file.write('amo, amas, amat, amamum, amatis, amant\n')
        cls.bad_config_file.file.flush()

        cls.missing_adapter_file = NamedTemporaryFile(mode='w+')
        cls.missing_adapter_config = SafeConfigParser()

        cls.missing_adapter_config.add_section('server')
        cls.missing_adapter_config.set('server', 'adapters', 'missing')
        cls.missing_adapter_config.set('server', 'debug_mode', '1')

        cls.missing_adapter_config.add_section('adapter.missing')
        cls.missing_adapter_config.set('adapter.missing', 'dummy', 'nothing')

        cls.missing_adapter_config.write(cls.missing_adapter_file)
        cls.missing_adapter_file.file.flush()

    @classmethod
    def teardown_class(cls):

        cls.test_config_file.close()
        cls.bad_config_file.close()


    def setup(self):

        self.cp = ConfigParser()

    def test_default_parser(self):

        # A default config parser should have at least a config option
        assert('config' in self.cp)

    def test_supplied_args(self):

        port = 8989
        addr = '127.0.0.1'
        default_opt_val = False

        self.cp.define('http_addr', default='0.0.0.0', option_help='Set HTTP server address')
        self.cp.define('http_port', default=8888, option_help='Set HTTP server port')
        self.cp.define('default_opt', default=default_opt_val, option_help='Default option')

        test_args=['prog_name', '--http_port', str(port), '--http_addr', str(addr)]

        self.cp.parse(test_args)

        assert_equal(self.cp.http_port, port)
        assert_equal(self.cp.http_addr, addr)
        assert_equal(self.cp.default_opt, default_opt_val)

    def test_imports_tornado_opts(self):

        test_args=['prog_name']

        self.cp.parse(test_args)

        tornado_opts = tornado.options.options._options

        for opt in tornado_opts:
            if tornado_opts[opt].name != 'help':
                assert_true(tornado_opts[opt].name in self.cp)

    def test_version_arg_handling(self):

        test_args = ['prog_name', '--version']

        with assert_raises(SystemExit) as cm:
            with self.capture_sys_output() as (stdout, stderr):
                self.cp.parse(test_args)

        assert_regexp_matches(stdout.getvalue(), 'odin server')
        assert_equal(cm.exception.code, 0)

    def test_ignores_undefined_arg(self):

        test_args = ['prog_name', '--ignored', '1234']

        self.cp.parse(test_args)

        assert_false('ignored' in self.cp)

    def test_parser_iterator(self):

        self.cp.parse()

        parser_opts = [opt for opt in self.cp]
        assert_true(len(parser_opts) > 0)

    def test_mismatched_arg_type(self):

        self.cp.define('intopt', default=1234, option_type=int, option_help='This is an integer option')
        test_args = ['prog_name', '--intopt', 'wibble']

        with assert_raises(SystemExit) as cm:
            with self.capture_sys_output() as (stdout, stderr):
                self.cp.parse(test_args)

        assert_equal(cm.exception.code, 2)

    def test_parse_file(self):

        self.cp.define('debug_mode', default=False, option_type=bool, option_help='Enable tornado debug mode')

        test_args = ['prog_name', '--config', self.test_config_file.name]

        self.cp.parse(test_args)

        assert_equal(self.cp.debug_mode, True)

    def test_parse_missing_file(self):

        config_file = 'missing.cfg'
        config_path = os.path.join(os.path.dirname(__file__), config_file)

        test_args = ['prog_name', '--config', config_path]

        with assert_raises_regexp(ConfigError,
                'Failed to parse configuration file: \[Errno 2\] No such file or directory'):
            self.cp.parse(test_args)

    def test_parse_bad_file(self):

        test_args = ['prog_name', '--config', self.bad_config_file.name]

        with assert_raises_regexp(ConfigError,
                  'Failed to parse configuration file: File contains no section headers'):
            self.cp.parse(test_args)

    def test_multiple_arg_parse(self):

        multiarg_list = ['dummy1', 'dummy2', 'dummy3']
        multiarg_str = ','.join(multiarg_list)

        split_args = _parse_multiple_arg(multiarg_str, arg_type=str, splitchar=',')

        assert_equal(len(multiarg_list), len(split_args))
        for (elem_in, elem_out) in zip(multiarg_list, split_args):
            assert_equal(elem_in, elem_out)

    def test_mismatched_multiple_arg_parse(self):

        multiarg_list = ['123', 'dummy2', 'dummy3']
        multiarg_str = ','.join(multiarg_list)

        with assert_raises_regexp(ConfigError,
                  'Multiple-valued argument contained element of incorrect type'):
            _parse_multiple_arg(multiarg_str, arg_type=int, splitchar=',')

    def test_multiple_option(self):

        self.cp.define('intvals', option_type=int, multiple=True, option_help='Integer list')

        adapter_list = ['dummy', 'dummy2 ', 'dummy3']
        adapter_str = ','.join(adapter_list)

        int_list = ['123', '456']
        int_str = ','.join(int_list)

        test_args = ['prog_name', '--adapters', adapter_str, '--intvals', int_str]

        self.cp.parse(test_args)

        assert_true('adapters' in self.cp)
        assert_equal(type(self.cp.adapters), type(adapter_list))
        assert_equal(len(self.cp.adapters), len(adapter_list))

        assert_true('intvals' in self.cp)
        assert_equal(type(self.cp.intvals), type(int_list))
        assert_equal(len(self.cp.intvals), len(int_list))

    def test_bad_multiple_option(self):

        self.cp.define('intvals', option_type=int, multiple=True, option_help='Integer list')

        bad_list = ['123', '456', 'oops']
        bad_str = '.'.join(bad_list)

        test_args = ['prog_name', '--intvals', bad_str]

        with assert_raises_regexp(ConfigError,
                  'Multiple-valued argument contained element of incorrect type'):
            self.cp.parse(test_args)

    def test_multiple_option_in_file(self):

        test_args = ['prog_name', '--config', self.test_config_file.name]

        self.cp.parse(test_args)

        assert_true('adapters' in self.cp)
        assert_equal(type(self.cp.adapters), list)

    def test_option_type_not_in_map(self):

        class StrWrapper(str):
            pass

        self.cp.define('wrapped', option_type=StrWrapper, option_help='Wrapped String')

        test_args = ['prog_name', '--config', self.test_config_file.name]

        self.cp.parse(test_args)
        assert_equal(self.cp.wrapped, 'wrapped_str')

    def test_parser_with_no_config_for_adapters(self):

        self.cp.parse()

        with assert_raises_regexp(ConfigError,
                'No configuration file parsed, unable to resolve adapters'):
            self.cp.resolve_adapters(adapter_list=['dummy', 'dummy2'])

    def test_parser_with_adapters_disabled(self):

        noadapter_cp = ConfigParser(has_adapters=False)
        noadapter_cp.parse()

        with assert_raises_regexp(
                ConfigError,
                'Configuration parser has no adapter option set'):
            noadapter_cp.resolve_adapters()

    def test_parser_with_no_adapters(self):

        self.cp.define('summy', option_type=bool, option_help='Dummy option')

        test_args = ['prog_name', '--dummy', '1']
        self.cp.parse(test_args)

        with assert_raises_regexp(
                ConfigError,
                'No adapters specified in configuration'):
            self.cp.resolve_adapters()

    def test_parser_no_config_file_for_adapters(self):

        test_args = ['prog_name', '--adapters', 'dummy']
        self.cp.parse(test_args)

        with assert_raises_regexp(
                ConfigError,
                'No configuration file parsed, unable to resolve adapters'):
            self.cp.resolve_adapters()

    def test_parser_config_missing_adapter_module(self):

        test_args = ['prog_name', '--config', self.missing_adapter_file.name]
        self.cp.parse(test_args)

        with assert_raises_regexp(
            ConfigError,
            'Configuration file has no module parameter for adapter missing'
        ):
            self.cp.resolve_adapters()

    def test_resolve_adapters(self):

        test_args = ['prog_name', '--config', self.test_config_file.name]

        self.cp.parse(test_args)

        assert_equal(self.cp.adapters, self.test_config_adapter_list)

        with assert_raises_regexp(ConfigError,
                  'Configuration file has no section for adapter '):
            self.cp.resolve_adapters(adapter_list=['dummy', 'missing'])

        adapters = self.cp.resolve_adapters()

        for adapter in adapters:
            assert_equal(type(adapters[adapter]), AdapterConfig)

            for option in self.test_config_adapter_options[adapter]:
                assert_equal(self.test_config_adapter_options[adapter][option],
                             getattr(adapters[adapter], option))

from nose.tools import *
import tornado.options

import sys
import os
from contextlib import contextmanager
from StringIO import StringIO

from odin.config.parser import ConfigParser, ConfigOption, ConfigError


class TestConfigOption():


    def test_simple_option(self):

        opt_name = 'simple'
        opt_type = bool
        opt_default = True

        opt = ConfigOption(opt_name, opt_type, opt_default)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.type, opt_type)
        assert_equal(opt.default, opt_default)

    def test_option_with_only_name(self):

        opt_name = 'simple'

        opt = ConfigOption(opt_name)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.type, str)
        assert_equal(opt.default, None)

    def test_option_with_default(self):

        opt_name = 'simple'
        opt_default = 'easy, huh?'

        opt = ConfigOption(opt_name, default=opt_default)

        assert_equal(opt.name, opt_name)
        assert_equal(opt.default, opt_default)
        assert_equal(opt.type, opt_default.__class__)

    def test_option_with_wrong_default_type(self):

        opt_name = 'simple'
        opt_default = 1234
        opt_type = bool

        with assert_raises(ConfigError) as cm:
            opt = ConfigOption(opt_name, type=opt_type, default=opt_default)
        assert_equal(str(cm.exception),
             'Default value {} for option {} does not have correct type ({})'.format(
                 opt_default, opt_name, opt_type
             ))


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

    def setup(self):

        self.cp = ConfigParser()

    def test_default_parser(self):

        # A default config parser should have at least a config option
        assert('config' in self.cp)

    def test_supplied_args(self):

        port = 8989
        addr = '127.0.0.1'
        default_opt_val = False

        self.cp.define('http_addr', default='0.0.0.0', help='Set HTTP server address')
        self.cp.define('http_port', default=8888, help='Set HTTP server port')
        self.cp.define('default_opt', default=default_opt_val, help='Default option')

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

    def test_ignores_undefined_arg(self):

        test_args = ['prog_name', '--ignored', '1234']

        self.cp.parse(test_args)

        assert_false('ignored' in self.cp)

    def test_mismatched_arg_type(self):

        self.cp.define('intopt', default=1234, type=int, help="This is an integer option")
        test_args = ['prog_name', '--intopt', 'wibble']

        with assert_raises(SystemExit) as cm:
            with self.capture_sys_output() as (stdout, stderr):
                self.cp.parse(test_args)

        assert_true(cm.exception.code, 2)

    def test_parse_file(self):

        config_file = 'test.cfg'
        config_path = os.path.join(os.path.dirname(__file__), config_file)

        self.cp.define('debug_mode', default=False, type=bool, help='Enable tornado debug mode')

        test_args = ['prog_name', '--config', config_path]

        self.cp.parse(test_args)

        assert_equal(self.cp.debug_mode, True)

    def test_parse_missing_file(self):

        config_file = 'missing.cfg'
        config_path = os.path.join(os.path.dirname(__file__), config_file)

        test_args = ['prog_name', '--config', config_path]

        with assert_raises(ConfigError) as cm:
            self.cp.parse(test_args)
        assert_equals(str(cm.exception),
              'Failed to parse configuration file: [Errno 2] No such file or directory: \'{}\''.format(
                  config_path
              ))

    def test_parse_bad_file(self):

        config_file = 'bad.cfg'
        config_path = os.path.join(os.path.dirname(__file__), config_file)

        test_args = ['prog_name', '--config', config_path]

        with assert_raises_regexp(ConfigError,
                  "Failed to parse configuration file: File contains no section headers") as cm:
            self.cp.parse(test_args)

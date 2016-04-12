from nose.tools import *
import tornado.options

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

    def test_default_parser(self):

        cp = ConfigParser()

        # A default config parser should have at least a config option
        assert('config' in cp)

    def test_supplied_args(self):

        port = 8989
        addr = '127.0.0.1'
        default_opt_val = False

        cp = ConfigParser()
        cp.define('http_addr', default='0.0.0.0', help='Set HTTP server address')
        cp.define('http_port', default=8888, help='Set HTTP server port')
        cp.define('default_opt', default=default_opt_val, help='Default option')

        test_args=['prog_name', '--http_port', str(port), '--http_addr', str(addr)]

        cp.parse(test_args)

        assert_equal(cp.http_port, port)
        assert_equal(cp.http_addr, addr)
        assert_equal(cp.default_opt, default_opt_val)

    def test_imports_tornado_opts(self):

        cp = ConfigParser()

        test_args=['prog_name']

        cp.parse(test_args)

        tornado_opts = tornado.options.options._options

        for opt in tornado_opts:
            if tornado_opts[opt].name != 'help':
                assert_true(tornado_opts[opt].name in cp)

    def test_ignores_undefined_arg(self):

        cp = ConfigParser()

        test_args = ['prog_name', '--ignored', '1234']

        cp.parse(test_args)

        assert_false('ignored' in cp)

    def test_mistmached_arg_type(self):
        pass


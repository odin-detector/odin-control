# Getting started with odin-control

---

## Installation

odin-control can be installed into your python environment with the following command:

```bash
pip install odin-control
```

For more detailed information and alternative installation methods, see the [Installation Guide].

## Running odin-control

You can verify that odin-control has been correctly installed into your python environment with
the following command:

```bash
$ odin_control --version
odin control version <installed version shown here>
```

odin-control requires configuration to do anything useful. You can get help with its command-line
options in the usual way:

```bash
$ odin_control --help
usage: odin_control [-h] [--version] [--config FILE] [--adapters ADAPTERS] [--http_addr HTTP_ADDR] [--http_port HTTP_PORT] [--enable_http ENABLE_HTTP]
                    [--https_port HTTPS_PORT] [--enable_https ENABLE_HTTPS] [--ssl_cert_file SSL_CERT_FILE] [--ssl_key_file SSL_KEY_FILE] [--debug_mode DEBUG_MODE]
                    [--access_logging debug|info|warning|error|none] [--static_path STATIC_PATH] [--enable_cors ENABLE_CORS] [--cors_origin CORS_ORIGIN]
                    [--api_version API_VERSION] [--graylog_server GRAYLOG_SERVER] [--graylog_logging_level GRAYLOG_LOGGING_LEVEL]
                    [--graylog_static_fields GRAYLOG_STATIC_FIELDS] [--log_file_max_size LOG_FILE_MAX_SIZE] [--log_file_num_backups LOG_FILE_NUM_BACKUPS]
                    [--log_file_prefix PATH] [--log_rotate_interval LOG_ROTATE_INTERVAL] [--log_rotate_mode LOG_ROTATE_MODE] [--log_rotate_when LOG_ROTATE_WHEN]
                    [--log_to_stderr LOG_TO_STDERR] [--logging debug|info|warning|error|none]

options:
  -h, --help            show this help message and exit
  --version             Show the server version information and exit
  --config FILE         Specify a configuration file to parse
  --adapters ADAPTERS   Comma-separated list of API adapters to load

<... snip ...>
```
See [Configuration] for details on the meaning of each options. The typical way to
configure odin-control is to specify a configuration file with the `--config
option:

```bash
odin_control --config <config_file_name>
```
where `config_file_name` points to a INI-style configuration file on your host. You can create a
simple example by pasting the follwing into a file (called, for example `test.cfg`):

``` ini title="test.cfg"
[server]
debug_mode = 1
http_port  = 8888
http_addr  = 127.0.0.1
static_path = static
adapters   = system_info

[tornado]
logging = debug

[adapter.system_info]
module = odin_control.adapters.system_info.SystemInfoAdapter
```
and running odin_control with that file:

```bash
odin-control --config test.cfg
```
which will result in output logged to the terminal:

```
[D YYMMDD hh:mm:dd selector_events:64] Using selector: KqueueSelector
[D YYMMDD hh:mm:dd adapter:62] SystemInfoAdapter loaded
[D YYMMDD hh:mm:dd api:103] Registered API adapter class SystemInfoAdapter from module odin_control.adapters.system_info for path system_info
[D YYMMDD hh:mm:dd adapter:73] SystemInfoAdapter initialize called with 1 adapters
[W YYMMDD hh:mm:dd default:38] Default handler static path does not exist: static
[I YYMMDD hh:mm:dd server:81] HTTP server listening on 127.0.0.1:8888
```

!!! note
    You can safely ignore the warning `"Default handler static path does not exist"` - more on that
    later.

!!! warning
    In the example, the `http_addr` parameter in the configuration limits access to the local loopback network
    interface (`127.0.0.1`). You can modify this to suit but **exercise caution** if exposing your odin-control
    instance to the wider network.


[Installation Guide]: user-guide/installation.md
[Configuration]: user-guide/configuration.md

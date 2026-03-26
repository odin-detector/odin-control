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
configure odin-control is to specify a configuration file with the `--config`
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
    In the example, the `http_addr` parameter in the configuration limits access to the local
    loopback network interface (`127.0.0.1`). You can modify this to suit your own environment
    but **exercise caution** if exposing your odin-control instance to the wider network.

You can leave odin_control running to follow the next sections of this guide, or shut it down using
the usual key sequence, e.g. `Ctrl-C`.

## Interacting with an API

You can now interact with an API provided by odin-control with a suitable client application.
[Curl](https://curl.se/) is commonly used and widely available, but we recommend
[httpie](https://httpie.io/cli) for ease of use; it can be installed as a standalone application or
into your python virtual environment if you prefer.

For instance, so see what [API adapters](user-guide/key-concepts.md#adapters) are loaded, enter the
following command:

```bash
http http://127.0.0.1:8888/api/adapters
```

which will return output like the following:

```json
HTTP/1.1 200 OK
Content-Length: 143
Content-Type: application/json; charset=UTF-8
Date: Fri, 06 Mar 2026 09:25:29 GMT
Etag: "38fdbbb91794fef1105f7ff38f1f60f92c277559"
Server: TornadoServer/6.4.1

{
    "adapters": {
        "system_info": {
            "module": "odin_control.adapters.system_info.SystemInfoAdapter",
            "version": "2.0.0"
        }
    }
}
```
!!! note
    An equivalent command using curl would be:

    `curl -s http://127.0.0.1:8888/api/adapters | python -m json.tool`.

    Piping the output to `python -m json.tool` formats the response for better readability.

Note that the response from odin-control is JSON-formatted; this is the common content type used to
interact with APIs in odin-control. The `./api/adapters` endpoint is bulit into odin-control and
returns information about the loaded adapters, which python package and module they are provided by,
and version information. This allows a client to interrogate a running instance to determine what is
loaded. In this case a single adapter `system_info` is loaded, which is provided by the odin-control
package itself.

To interact with the `system_info` adapter API, enter the following command:

```bash
http http://127.0.0.1:8888/api/system_info
```

which will return the following (with HTTP headers removed for clarity):

```json
{
    "description": "Information about the system hosting this odin server instance",
    "name": "system_info",
    "odin_version": "2.0.0",
    "platform": {
        "description": "Information about the underlying platform",
        "name": "platform",
        "node": "hostname.example.com",
        "processor": "arm",
        "release": "25.3.0",
        "system": "Darwin",
        "version": "Darwin Kernel Version 25.3.0: Wed Jan 28 20:53:05 PST 2026; root:xnu-12377.81.4~5/RELEASE_ARM64_T6020"
    },
    "python_version": "3.12.11",
    "server_uptime": 7106.5337200164795,
    "tornado_version": "6.4.1"
}
```
odin-control makes it possible to drill down into the structure provided by an adapter by extending
the requested URL path. For instance, to retrieve just the `server_uptime` value, enter the
following:

```bash
http http://127.0.0.1:8888/api/system_info/server_uptime
```

which will return just the value of the `server_uptime` parameter:

```json
{
    "value": 7646.556041955948
}
```
Similarly, a subtree of the API can be retrieved. For instance:

```bash
http http://127.0.0.1:8888/api/system_info/platform
```

returns the `platform` subtree:

```json
{
    "description": "Information about the underlying platform",
    "name": "platform",
    "node": "hostname.example.com",
    "processor": "arm",
    "release": "25.3.0",
    "system": "Darwin",
    "version": "Darwin Kernel Version 25.3.0: Wed Jan 28 20:53:05 PST 2026; root:xnu-12377.81.4~5/RELEASE_ARM64_T6020"
}
```

## Modifying state

So far, all the interaction with odin-control has been to read the state an adapter. In a REST-like
API this corresponds to making HTTP GET requests. To modify the state of one or more parameters in
an adapter, PUT requests are used with a JSON payload containing the new values.

The `system_info` adapter used above does not expose any read-write parameters. A simple example is
available in the [odin-workshop](http://github.com/stfc-aeg/odin-workshop) repository. To use this,
first clone the repository:

```bash
git clone https://github.com/stfc-aeg/odin-workshop
```

Change directory to the location of the example adapter:

```bash
cd python
```

and install the adapter into your python environment (where odin-control is already installed):

```
pip install .
```

!!! note
    If you wish to try modifying the adapter code, it can also be installed in
    [editable mode](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs)
    by using the `-e` command option.

The repository also contains an
[example configuration file](https://github.com/stfc-aeg/odin-workshop/blob/main/python/test/config/workshop.cfg),
or you can create it yourself:


```ini title="workshop.cfg"
[server]
debug_mode = 1
http_port  = 8888
http_addr  = 127.0.0.1
static_path = test/static
adapters   = workshop, system_info

[tornado]
logging = debug

[adapter.workshop]
module = workshop.adapter.WorkshopAdapter
background_task_enable = 1
background_task_interval = 1.0

[adapter.system_info]
module = odin_control.adapters.system_info.SystemInfoAdapter
```

!!! Note
    This configuration also loads the `system_info` adapter and shows how multiple adapters can
    be run and configured.

Run odin-control with this configuration:

```bash
odin_control --config workshop.cfg
```

and note that the output shows the adapter incrementing in two background tasks:

```
[D YYMMDD hh:mm:ss selector_events:64] Using selector: KqueueSelector
[D YYMMDD hh:mm:ss adapter:62] WorkshopAdapter loaded
[D YYMMDD hh:mm:ss controller:120] Launching background tasks with interval 1.00 secs
[D YYMMDD hh:mm:ss adapter:41] WorkshopAdapter loaded
[D YYMMDD hh:mm:ss api:101] Registered API adapter class WorkshopAdapter from module workshop.adapter for path workshop
[D YYMMDD hh:mm:ss adapter:62] SystemInfoAdapter loaded
[D YYMMDD hh:mm:ss api:101] Registered API adapter class SystemInfoAdapter from module odin_control.adapters.system_info for path system_info
[D YYMMDD hh:mm:ss adapter:73] WorkshopAdapter initialize called with 2 adapters
[W YYMMDD hh:mm:ss adapter:83] WorkshopAdapter controller has no initialize method
[D YYMMDD hh:mm:ss adapter:73] SystemInfoAdapter initialize called with 2 adapters
[D YYMMDD hh:mm:ss default:40] Static path for default handler is test/static
[I YYMMDD hh:mm:ss server:81] HTTP server listening on 127.0.0.1:8888
[D YYMMDD hh:mm:ss controller:148] Background IOLoop task running, count = 0
[D YYMMDD hh:mm:ss controller:167] Background thread task running, count = 0
[D YYMMDD hh:mm:ss controller:148] Background IOLoop task running, count = 1
[D YYMMDD hh:mm:ss controller:167] Background thread task running, count = 1
[D YYMMDD hh:mm:ss controller:148] Background IOLoop task running, count = 2
[D YYMMDD hh:mm:ss controller:167] Background thread task running, count = 2
```

The adapter exposes a sub-tree of parameters related to the background tasks:

```bash
http http://128.0.0.1:8888/api/workshop/background_task
```

returns:

```json
{
    "enable": true,
    "interval": 1.0,
    "ioloop_count": 418,
    "thread_count": 417
}
```

The `enable` and `interval` parameters are read-write in this instance. You can stop the background
tasks by setting `enable` to `false` using a PUT request:

```bash
http PUT http://127.0.0.1:8888/api/workshop/background_task enable:=false
```

!!! note
    This command is using httpie's implicit JSON support and
    [JSON field syntax](https://httpie.io/docs/cli/non-string-json-fields) to create the
    PUT request body. The equivalent `curl` command is (the much more verbose):
    ```bash
    curl -X PUT http://127.0.0.1:8888/api/workshop/background_task -H "Content-Type: application/json" -d '{"enable": false}'
    ```

The output will show the background tasks stopping and no futher status reports:

```
[D YYMMDD hh:mm:ss server:141] 200 PUT /api/workshop/background_task (127.0.0.1) 1.13ms
[D YYMMDD hh:mm:ss controller:172] Background thread task stopping
```

You can also increase the speed of the counters by setting the interval:

```bash
http PUT http://127.0.0.1:8888/api/workshop/background_task interval:=0.5
```

and re-enabling the tasks:
```bash
http PUT http://127.0.0.1:8888/api/workshop/background_task enable:=true
```

which will give the following output:

```
[D YYMMDD hh:mm:ss controller:105] Setting background task interval to 0.500000
[D YYMMDD hh:mm:ss adapter:91] {'ioloop_count': 535, 'thread_count': 533, 'enable': False, 'interval': 0.5}
[D YYMMDD hh:mm:ss server:141] 200 PUT /api/workshop/background_task (127.0.0.1) 2.62ms
[D YYMMDD hh:mm:ss controller:120] Launching background tasks with interval 0.50 secs
[D YYMMDD hh:mm:ss adapter:91] {'ioloop_count': 535, 'thread_count': 533, 'enable': True, 'interval': 0.5}
[D YYMMDD hh:mm:ss server:141] 200 PUT /api/workshop/background_task (127.0.0.1) 0.85ms
[D YYMMDD hh:mm:ss controller:148] Background IOLoop task running, count = 540
[D YYMMDD hh:mm:ss controller:167] Background thread task running, count = 540
[D YYMMDD hh:mm:ss controller:148] Background IOLoop task running, count = 560
[D YYMMDD hh:mm:ss controller:167] Background thread task running, count = 560
```
Note that the task count messages appear twice as frequently.

## Going further

Refer to the [user guide] to learn more about installation, configuration and the key concepts of
odin-control. The [developer guide] explains more details on how to implement adapters for
controlling systems.

[Installation Guide]: user-guide/installation.md
[Configuration]: user-guide/configuration.md
[User Guide]: user-guide/index.md
[Developer Guide]: developer-guide/index.md

PyGripControl
=============
Author: Justin Karneges <justin@fanout.io>

GRIP library for Python.

Requirements
------------

* jwt
* pubcontrol

Install
-------

You can install from PyPi:

    sudo pip install gripcontrol

Or from this repository:

    sudo python setup.py install

Sample Usage
------------

Examples for how to publish HTTP response and HTTP stream messages to GRIP proxy endpoints via the GripPubControl class.

```python
from base64 import b64decode
from pubcontrol import PubControlClient
from gripcontrol import GripPubControl

def callback(result, message):
    if result:
        print('Publish successful')
    else:
        print('Publish failed with message: ' + message)

# GripPubControl can be initialized with or without an endpoint configuration.
# Each endpoint can include optional JWT authentication info.
# Multiple endpoints can be included in a single configuration.

grippub = GripPubControl({ 
        'control_uri': 'https://api.fanout.io/realm/<myrealm>',
        'control_iss': '<myrealm>',
        'key': b64decode('<myrealmkey>')})

# Add new endpoints by applying an endpoint configuration:
grippub.apply_grip_config([{'control_uri': '<myendpoint_uri_1>'}, 
        {'control_uri': '<myendpoint_uri_2>'}])

# Remove all configured endpoints:
grippub.remove_all_clients()

# Explicitly add an endpoint as a PubControlClient instance:
pubclient = PubControlClient('<myendpoint_uri>')
# Optionally set JWT auth: pubclient.set_auth_jwt('<claim>', '<key>')
# Optionally set basic auth: pubclient.set_auth_basic('<user>', '<password>')
grippub.add_client(pubclient)

# Publish across all configured endpoints:
grippub.publish_http_response('<channel>', 'Test publish!')
grippub.publish_http_response('<channel>', 'Test async publish!',
        blocking=False, callback=callback)
grippub.publish_http_stream('<channel>', 'Test publish!')
grippub.publish_http_stream('<channel>', 'Test async publish!',
        blocking=False, callback=callback)

# Wait for all async publish calls to complete:
grippub.finish
```

Validate the Grip-Sig request header from incoming GRIP messages. This ensures that the message was sent from a valid source and is not expired. Note that when using Fanout.io the key is the realm key, and when using Pushpin the key is configurable in Pushpin's settings.

```python
from gripcontrol import validate_sig

is_valid = validate_sig(request['Grip-Sig'], '<key>')
```

Long polling example via response _headers_ using the WEBrick gem. The client connects to a GRIP proxy over HTTP and the proxy forwards the request to the origin. The origin subscribes the client to a channel and instructs it to long poll via the response _headers_. Note that with the recent versions of Apache it's not possible to send a 304 response containing custom headers, in which case the response body should be used instead (next usage example below).

```python
try:
    # Python 2.x:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 3.x:
    from http.server import BaseHTTPRequestHandler, HTTPServer

from gripcontrol import create_grip_channel_header, validate_sig

class GripHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Validate the Grip-Sig header:
        if validate_sig(self.headers.get('Grip-Sig'), '<key>') is False:
            return
        # Instruct the client to long poll via the response headers:
        self.send_response(200)
        self.send_header('Grip-Hold', 'response')
        self.send_header('Grip-Channel',
                create_grip_channel_header('<channel>'))
        self.end_headers()

server = HTTPServer(('', 80), GripHandler)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
```

Long polling example via response _body_ using the WEBrick gem. The client connects to a GRIP proxy over HTTP and the proxy forwards the request to the origin. The origin subscribes the client to a channel and instructs it to long poll via the response _body_.

```python
try:
    # Python 2.x:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 3.x:
    from http.server import BaseHTTPRequestHandler, HTTPServer

from gripcontrol import create_hold_response, validate_sig

class GripHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Validate the Grip-Sig header:
        if validate_sig(self.headers.get('Grip-Sig'), '<key>') is False:
            return

        # Instruct the client to long poll via the response body:
        self.send_response(200)
        self.send_header('Content-Type', 'application/grip-instruct')
        self.end_headers()
        self.wfile.write(create_hold_response('<channel>').encode('utf-8'))

server = HTTPServer(('', 80), GripHandler)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
```

WebSocket example using the WEBrick gem and WEBrick WebSocket gem extension. A client connects to a GRIP proxy via WebSockets and the proxy forward the request to the origin. The origin accepts the connection over a WebSocket and responds with a control message indicating that the client should be subscribed to a channel. Note that in order for the GRIP proxy to properly interpret the control messages, the origin must provide a 'grip' extension in the 'Sec-WebSocket-Extensions' header. This is accomplished in the WEBrick WebSocket gem extension by adding the following line to lib/webrick/websocket/server.rb and rebuilding the gem: res['Sec-WebSocket-Extensions'] = 'grip; message-prefix=""'

```python

```

WebSocket over HTTP example using the WEBrick gem. In this case, a client connects to a GRIP proxy via WebSockets and the GRIP proxy communicates with the origin via HTTP.

```python

```

Parse a GRIP URI to extract the URI, ISS, and key values. The values will be returned in a hash containing 'control_uri', 'control_iss', and 'key' keys.

```python
from gripcontrol import parse_grip_uri

config = parse_grip_uri(
    'http://api.fanout.io/realm/<myrealm>?iss=<myrealm>' +
    '&key=base64:<myrealmkey>')
```

PyGripControl
=============
Author: Justin Karneges <justin@fanout.io>, Konstantin Bokarius <kon@fanout.io>

GRIP library for Python.

Requirements
------------

* jwt
* pubcontrol

For ZMQ publishing:

* pyzmq
* tnetstring

Install
-------

You can install from PyPi:

    sudo pip install gripcontrol

Or from this repository:

    sudo python setup.py install

Sample Usage
------------

Examples for how to publish HTTP response and HTTP stream messages to GRIP proxy endpoints via the GripPubControl class. Note that the GripPubControl class also supports publishing to ZMQ PUSH and XPUB sockets.

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

# Add a ZMQ command URI endpoint for automatic PUSH/XPUB socket discovery
# and indicate that the XPUB socket should be used via require_subscribers.
# NOTE: the pyzmq and tnetstring packages must be installed for ZMQ publishing.
grippub.apply_grip_config({'control_zmq_uri': 'tcp://localhost:5563',
        'require_subscribers': True})

# Remove all configured endpoints:
grippub.remove_all_clients()

# Explicitly add an endpoint as a PubControlClient instance:
pubclient = PubControlClient('<myendpoint_uri>')
# Optionally set JWT auth: pubclient.set_auth_jwt(<claim>, '<key>')
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
grippub.finish()
```

Validate the Grip-Sig request header from incoming GRIP messages. This ensures that the message was sent from a valid source and is not expired. Note that when using Fanout.io the key is the realm key, and when using Pushpin the key is configurable in Pushpin's settings.

```python
from gripcontrol import validate_sig

is_valid = validate_sig(request['Grip-Sig'], '<key>')
```

Long polling example via response _headers_. The client connects to a GRIP proxy over HTTP and the proxy forwards the request to the origin. The origin subscribes the client to a channel and instructs it to long poll via the response _headers_. Note that with the recent versions of Apache it's not possible to send a 304 response containing custom headers, in which case the response body should be used instead (next usage example below).

```python
try:
    # Python 3.x:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 2.x:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

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
        # To optionally set a timeout value in seconds:
        # self.send_header('Grip-Timeout', <timeout_value>)
        self.end_headers()

server = HTTPServer(('', 80), GripHandler)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
```

Long polling example via response _body_. The client connects to a GRIP proxy over HTTP and the proxy forwards the request to the origin. The origin subscribes the client to a channel and instructs it to long poll via the response _body_.

```python
try:
    # Python 3.x:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 2.x:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

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
        # Or to optionally set a timeout value in seconds:
        # self.wfile.write(create_hold_response(
        #         '<channel>', timeout=<timeout_value>).encode('utf-8'))
server = HTTPServer(('', 80), GripHandler)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
```

WebSocket example using the Tornado 4.0.2 module. A client connects to a GRIP proxy via WebSockets and the proxy forward the request to the origin. The origin accepts the connection over a WebSocket and responds with a control message indicating that the client should be subscribed to a channel. Note that in order for the GRIP proxy to properly interpret the control messages, the origin must provide a 'grip' extension in the 'Sec-WebSocket-Extensions' header. This is accomplished by overriding the 'get' method in the handler and implementing a custom WebSocketProtocol class. Also note that a significant amount of code was removed from the 'get' and '_accept_connection' methods for the sake of readability and should be replaced if using this code in a real environment.

```python
import threading, time
import tornado.httpserver, tornado.websocket, tornado.ioloop, tornado.web
from tornado.websocket import WebSocketProtocol13
from pubcontrol import Item
from gripcontrol import websocket_control_message, GripPubControl
from gripcontrol import WebSocketMessageFormat

# Send a 'Sec-WebSocket-Extensions: grip; message-prefix=""' header to
# the GRIP proxy by extending the WebSocketProtocol13 class.
class WebSocketProtocolGrip(WebSocketProtocol13):
    def _accept_connection(self):
        self.stream.write(tornado.escape.utf8(
                "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
                "Connection: Upgrade\r\nSec-WebSocket-Accept: %s\r\n"
                "Sec-WebSocket-Extensions: grip; message-prefix=\"\"\r\n"
                "\r\n" % (self._challenge_response())))
        super(self.__class__, self)._run_callback(self.handler.open,
                *self.handler.open_args, **self.handler.open_kwargs)
        super(self.__class__, self)._receive_frame()

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def on_message(self, message):
        pass
 
    # Override the get method to have it use the WebSocketProtocolGrip class:
    def get(self, *args, **kwargs):
        self.open_args = args
        self.open_kwargs = kwargs
        self.stream = self.request.connection.detach()
        self.ws_connection = WebSocketProtocolGrip(self, None)
        self.ws_connection.accept_connection()

    def open(self):
        # Subscribe the WebSocket to a channel:
        self.write_message('c:' + websocket_control_message(
                'subscribe', {'channel': '<channel>'}))
        threading.Thread(target = self.publish_message).start()
       
    def publish_message(self):
        # Wait and then publish a message to the subscribed channel:
        time.sleep(3)
        grippub = GripPubControl({'control_uri': '<myendpoint>'})
        grippub.publish('<channel>',
                Item(WebSocketMessageFormat('Test WebSocket publish!!')))

if __name__ == "__main__":
    http_server = tornado.httpserver.HTTPServer(
            tornado.web.Application(
            [(r'/websocket', WebSocketHandler)]))
    http_server.listen(80)
    tornado.ioloop.IOLoop.instance().start()
```

WebSocket over HTTP example. In this case, a client connects to a GRIP proxy via WebSockets and the GRIP proxy communicates with the origin via HTTP.

```python
try:
    # Python 3.x:
    from http.server import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    # Python 2.x:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import threading, time
from pubcontrol import Item
from gripcontrol import decode_websocket_events, GripPubControl
from gripcontrol import encode_websocket_events, WebSocketEvent
from gripcontrol import websocket_control_message, validate_sig
from gripcontrol import WebSocketMessageFormat

class GripHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Validate the Grip-Sig header:
        if validate_sig(self.headers.get('Grip-Sig'), '<key>') is False:
            return

        # Set the headers required by the GRIP proxy:
        self.send_response(200)
        self.send_header('Sec-WebSocket-Extensions',
                'grip; message-prefix=""')
        self.send_header('Content-Type', 'application/websocket-events')
        self.end_headers()

        request_body = self.rfile.read(int(self.headers.get('Content-Length')))
        in_events = decode_websocket_events(request_body)
        if in_events[0].type == 'OPEN':
            # Open the WebSocket and subscribe it to a channel:
            out_events = []
            out_events.append(WebSocketEvent('OPEN'))
            out_events.append(WebSocketEvent('TEXT', 'c:' +
                    websocket_control_message('subscribe',
                    {'channel': '<channel>'})))
            self.wfile.write(encode_websocket_events(
                    out_events).encode('utf-8'))
            threading.Thread(target = self.publish_message).start()

    def publish_message(self):
        # Wait and then publish a message to the subscribed channel:
        time.sleep(3)
        grippub = GripPubControl({'control_uri': '<myendpoint>'})
        grippub.publish('<channel>',
                Item(WebSocketMessageFormat('Test WebSocket publish!!')))

server = HTTPServer(('', 80), GripHandler)
try:
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
```

Parse a GRIP URI to extract the URI, ISS, and key values. The values will be returned in a dictionary containing 'control_uri', 'control_iss', and 'key' keys.

```python
from gripcontrol import parse_grip_uri

config = parse_grip_uri(
    'http://api.fanout.io/realm/<myrealm>?iss=<myrealm>' +
    '&key=base64:<myrealmkey>')
```

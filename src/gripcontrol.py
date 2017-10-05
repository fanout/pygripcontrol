#    gripcontrol.py
#    ~~~~~~~~~
#    This module implements the GripControl functionality.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

# The GripControl class provides functionality that is used in conjunction
# with GRIP proxies. This includes facilitating the creation of hold
# instructions for HTTP long-polling and HTTP streaming, parsing GRIP URIs
# into config objects, validating the GRIP-SIG header coming from GRIP
# proxies, creating GRIP channel headers, and also WebSocket-over-HTTP
# features such as encoding/decoding web socket events and generating
# control messages.

import sys
from datetime import datetime
import calendar
from base64 import b64encode, b64decode
from copy import deepcopy
import json
import jwt
from .channel import Channel
from .response import Response
from .websocketevent import WebSocketEvent
from six.moves.urllib_parse import urlparse, parse_qs, urlencode


is_python3 = sys.version_info >= (3,)


# Parse the specified GRIP URI into a config object that can then be passed
# to the GripPubControl class. The URI can include 'iss' and 'key' JWT
# authentication query parameters as well as any other required query string
# parameters. The JWT 'key' query parameter can be provided as-is or in base64
# encoded format.
def parse_grip_uri(uri):
	parsed = urlparse(uri)
	params = parse_qs(parsed.query)
	iss = None
	key = None
	if 'iss' in params:
		iss = params['iss'][0]
		del params['iss']
	if 'key' in params:
		key = params['key'][0]
		del params['key']
	if key is not None and key.startswith('base64:'):
		key = b64decode(key[7:])
	qs = urlencode(params, True)
	path = parsed.path
	if path.endswith('/'):
		path = path[:-1]
	control_uri = parsed.scheme + '://' + parsed.netloc + path
	if qs:
		control_uri += '?' + qs
	out = {'control_uri': control_uri}
	if iss:
		out['control_iss'] = iss
	if key:
		out['key'] = key
	return out

# Validate the specified JWT token and key. This method is used to validate
# the GRIP-SIG header coming from GRIP proxies such as Pushpin or Fanout.io.
# Note that the token expiration is also verified.
def validate_sig(token, key):
	# jwt expects the token in utf-8
	if _is_unicode_instance(token):
		token = token.encode('utf-8')	

	try:
		claim = jwt.decode(token, key)
	except:
		return False

	exp = claim.get('exp')
	if not exp:
		return False

	if _timestamp_utcnow() >= exp:
		return False

	return True

# Create a GRIP channel header for the specified channels. The channels
# parameter can be specified as a string representing the channel name,
# a Channel instance, or an array of Channel instances. The returned GRIP
# channel header is used when sending instructions to GRIP proxies via
# HTTP headers.
def create_grip_channel_header(channels):
	channels = _parse_channels(channels)
	parts = list()
	for channel in channels:
		s = channel.name
		if channel.prev_id is not None:
			s += '; prev-id=%s' % channel.prev_id
		parts.append(s)
	return ', '.join(parts)

# Create GRIP hold instructions for the specified mode, channels, response
# and optional timeout value. The channel parameter can be specified as
# either a string representing the channel name, a Channel instance or an
# array of Channel instances. The response parameter can be specified as
# either a string representing the response body or a Response instance.
def create_hold(mode, channels, response, timeout=None):
	hold = dict()
	hold['mode'] = mode
	channels = _parse_channels(channels)
	ichannels = _get_hold_channels(channels)
	hold['channels'] = ichannels
	if timeout:
		hold['timeout'] = timeout
	iresponse = _get_hold_response(response)
	instruct = dict()
	instruct['hold'] = hold
	if iresponse:
		instruct['response'] = iresponse

	return json.dumps(instruct)

# A convenience method for creating GRIP hold response instructions for HTTP
# long-polling. This method simply passes the specified parameters to the
# create_hold method with 'response' as the hold mode.
def create_hold_response(channels, response=None, timeout=None):
	return create_hold('response', channels, response, timeout)

# A convenience method for creating GRIP hold stream instructions for HTTP
# streaming. This method simply passes the specified parameters to the
# create_hold method with 'stream' as the hold mode.
def create_hold_stream(channels, response=None):
	return create_hold('stream', channels, response)

# Decode the specified HTTP request body into an array of WebSocketEvent
# instances when using the WebSocket-over-HTTP protocol. A RuntimeError
# is raised if the format is invalid.
def decode_websocket_events(body):
	if is_python3:
		if not isinstance(body, bytes):
			raise ValueError('body must be bytes')

	out = list()
	start = 0
	while start < len(body):
		if is_python3:
			at = body.find(b'\r\n', start)
			if at == -1:
				raise ValueError('bad format')
			typeline = body[start:at]
			start = at + 2

			at = typeline.find(b' ')
			if at != -1:
				etype = typeline[:at].decode('utf-8')
				clen = int(b'0x' + typeline[at + 1:], 16)
				content = body[start:start + clen]
				start += clen + 2
				e = WebSocketEvent(etype, content)
			else:
				etype = typeline.decode('utf-8')
				e = WebSocketEvent(etype)
		else:
			at = body.find('\r\n', start)
			if at == -1:
				raise ValueError('bad format')
			typeline = body[start:at]
			start = at + 2

			at = typeline.find(' ')
			if at != -1:
				etype = typeline[:at]
				clen = int('0x' + typeline[at + 1:], 16)
				content = body[start:start + clen]
				start += clen + 2
				e = WebSocketEvent(etype, content)
			else:
				e = WebSocketEvent(typeline)

		out.append(e)

	return out

# Encode the specified array of WebSocketEvent instances. The returned string
# value should then be passed to a GRIP proxy in the body of an HTTP response
# when using the WebSocket-over-HTTP protocol.
def encode_websocket_events(events):
	if is_python3:
		out = b''
		for e in events:
			if isinstance(e.type, str):
				etype = e.type.encode('utf-8')
			else:
				etype = e.type
			content = e.content
			if content is not None:
				if isinstance(content, str):
					content = content.encode('utf-8')
				else:
					content = content
			out += etype
			if content is not None:
				size_str = ' %x' % len(content)
				out += size_str.encode('utf-8')
			out += b'\r\n'
			if content is not None:
				out += content
				out += b'\r\n'
		return out
	else:
		out = ''
		for e in events:
			if e.content is not None:
				out += '%s %x\r\n%s\r\n' % (e.type, len(e.content), e.content)
			else:
				out += '%s\r\n' % e.type
		return out

# Generate a WebSocket control message with the specified type and optional
# arguments. WebSocket control messages are passed to GRIP proxies and
# example usage includes subscribing/unsubscribing a WebSocket connection
# to/from a channel.
def websocket_control_message(type, args=None):
	if args:
		out = deepcopy(args)
	else:
		out = dict()
	out['type'] = type
	return json.dumps(out)

# Parse the specified parameter into an array of Channel instances. The
# specified parameter can either be a string, a Channel instance, or
# an array of Channel instances.
def _parse_channels(channels):
	if isinstance(channels, Channel):
		channels = [channels]
	elif _is_basestring_instance(channels):
		channels = [Channel(channels)]
	assert(len(channels) > 0)
	return channels

# Get an array of hashes representing the specified channels parameter. The
# resulting array is used for creating GRIP proxy hold instructions.
def _get_hold_channels(channels):
	ichannels = list()
	for c in channels:
		if _is_basestring_instance(c):
			c = Channel(c)

		ichannel = dict()
		ichannel['name'] = c.name
		if c.prev_id:
			ichannel['prev-id'] = c.prev_id
		ichannels.append(ichannel)
	return ichannels

# Get a hash representing the specified response parameter. The
# resulting hash is used for creating GRIP proxy hold instructions.
def _get_hold_response(response): 
	iresponse = None
	if response is not None:
		if _is_basestring_instance(response) or isinstance(response, bytes):
			response = Response(body=response)
		iresponse = dict()
		if response.code is not None:
			iresponse['code'] = response.code
		if response.reason:
			iresponse['reason'] = response.reason
		if response.headers:
			iresponse['headers'] = response.headers
		if response.body:
			is_text, val = _bin_or_text(response.body)
			if is_text:
				iresponse['body'] = val
			else:
				iresponse['body-bin'] = b64encode(val).decode('utf-8')
	return iresponse

# An internal method used for determining whether the specified instance
# is a unicode instance.
def _is_unicode_instance(instance):
	try:
		if isinstance(instance, unicode):
			return True
	except NameError:
		if isinstance(instance, str):
			return True
	return False

# An internal method used for determining whether the specified instance
# is a basestring instance.
def _is_basestring_instance(instance):
	try:
		if isinstance(instance, basestring):
			return True
	except NameError:
		if isinstance(instance, str):
			return True
	return False

# An internal method used for determining whether the specified string is
# is binary or text.
def _bin_or_text(s):
	if _is_unicode_instance(s):
		return (True, s)
	try:
		return (True, s.decode('utf-8'))
	except UnicodeDecodeError:
		return (False, s)

# An internal method used for getting the current UNIX UTC timestamp.
def _timestamp_utcnow():
	return calendar.timegm(datetime.utcnow().utctimetuple())

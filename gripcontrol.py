from datetime import datetime
import calendar
from urlparse import urlparse, parse_qs
from urllib import urlencode
from base64 import b64encode, b64decode
from copy import deepcopy
import json
import jwt
from pubcontrol import PubControl, PubControlClient, Item, Format

# returns (boolean is_text, string value)
def _bin_or_text(s):
	if isinstance(s, unicode):
		return (True, s)
	for c in s:
		i = ord(c)
		if i < 0x20 or i >= 0x7f:
			return (False, s)
	return (True, s.decode('utf-8'))

def _timestamp_utcnow():
	return calendar.timegm(datetime.utcnow().utctimetuple())

class Channel(object):
	def __init__(self, name, prev_id=None):
		self.name = name
		self.prev_id = prev_id

class Response(object):
	def __init__(self, code=None, reason=None, headers=None, body=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body

class HttpResponseFormat(Format):
	def __init__(self, code=None, reason=None, headers=None, body=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body

	def name(self):
		return 'http-response'

	def export(self):
		out = dict()
		if self.code is not None:
			out['code'] = self.code
		if self.reason:
			out['reason'] = self.reason
		if self.headers:
			out['headers'] = self.headers
		if self.body:
			is_text, val = _bin_or_text(self.body)
			if is_text:
				out['body'] = val
			else:
				out['body-bin'] = b64encode(val)
		return out

class HttpStreamFormat(Format):
	def __init__(self, content=None, close=False):
		self.content = content
		self.close = close
		if not self.close and self.content is None:
			raise ValueError('content not set')

	def name(self):
		return 'http-stream'

	def export(self):
		out = dict()
		if self.close:
			out['action'] = 'close'
		else:
			is_text, val = _bin_or_text(self.content)
			if is_text:
				out['content'] = val
			else:
				out['content-bin'] = b64encode(val)
		return out

class WebSocketMessageFormat(Format):
	def __init__(self, content, binary=False):
		self.content = content
		self.binary = binary

	def name(self):
		return 'ws-message'

	def export(self):
		out = dict()
		val = self.content
		if self.binary:
			if isinstance(val, unicode):
				val = val.encode('utf-8')
			out['content-bin'] = b64encode(val)
		else:
			if not isinstance(val, unicode):
				val = val.decode('utf-8')
			out['content'] = val
		return out

class GripPubControl(PubControl):
	def apply_grip_config(self, config):
		if not isinstance(config, list):
			config = [config]
		for entry in config:
			if 'control_uri' not in entry:
				continue
			client = PubControlClient(entry['control_uri'])
			if 'control_iss' in entry:
				client.set_auth_jwt({'iss': entry['control_iss']}, entry['key'])
			self.add_client(client)

	def publish_http_response(self, channel, http_response, id=None, prev_id=None, blocking=False, callback=None):
		if isinstance(http_response, basestring):
			http_response = HttpResponseFormat(body=http_response)
		item = Item(http_response, id, prev_id)
		super(GripPubControl, self).publish(channel, item, blocking=blocking, callback=callback)

	def publish_http_stream(self, channel, http_stream, id=None, prev_id=None, blocking=False, callback=None):
		if isinstance(http_stream, basestring):
			http_stream = HttpStreamFormat(http_stream)
		item = Item(http_stream, id, prev_id)
		super(GripPubControl, self).publish(channel, item, blocking=blocking, callback=callback)

class WebSocketEvent(object):
	def __init__(self, type, content=None):
		self.type = type
		self.content = content

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

def validate_sig(token, key):
	# jwt expects the token in utf-8
	if isinstance(token, unicode):
		token = token.encode('utf-8')

	try:
		claim = jwt.decode(token, key, verify_expiration=False)
	except:
		return False

	exp = claim.get('exp')
	if not exp:
		return False

	if _timestamp_utcnow() >= exp:
		return False

	return True

def create_grip_channel_header(channels):
	if isinstance(channels, Channel):
		channels = [channels]
	elif isinstance(channels, basestring):
		channels = [Channel(channels)]
	assert(len(channels) > 0)

	parts = list()
	for channel in channels:
		s = channel.name
		if channel.prev_id is not None:
			s += '; prev-id=%s' % channel.prev_id
		parts.append(s)
	return ', '.join(parts)

def create_hold(mode, channels, response):
	hold = dict()

	hold['mode'] = mode

	if isinstance(channels, Channel):
		channels = [channels]
	elif isinstance(channels, basestring):
		channels = [Channel(channels)]

	assert(len(channels) > 0)

	ichannels = list()
	for c in channels:
		if isinstance(c, basestring):
			c = Channel(c)

		ichannel = dict()
		ichannel['name'] = c.name
		if c.prev_id:
			ichannel['prev-id'] = c.prev_id
		ichannels.append(ichannel)

	hold['channels'] = ichannels

	iresponse = None
	if response is not None:
		if isinstance(response, basestring):
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
				iresponse['body-bin'] = b64encode(val)

	instruct = dict()
	instruct['hold'] = hold
	if iresponse:
		instruct['response'] = iresponse

	return json.dumps(instruct)

def create_hold_response(channels, response=None):
	return create_hold('response', channels, response)

def create_hold_stream(channels, response=None):
	return create_hold('stream', channels, response)

def decode_websocket_events(body):
	out = list()
	start = 0
	while start < len(body):
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

def encode_websocket_events(events):
	out = ''
	for e in events:
		if e.content is not None:
			out += '%s %x\r\n%s\r\n' % (e.type, len(e.content), e.content)
		else:
			out += '%s\r\n' % e.type
	return out

def websocket_control_message(type, args=None):
	if args:
		out = deepcopy(args)
	else:
		out = dict()
	out['type'] = type
	return json.dumps(out)

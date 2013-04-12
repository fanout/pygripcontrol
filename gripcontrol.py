from base64 import b64encode
from pubcontrol import PubControl, Item, Format
import json

# returns (boolean is_text, string value)
def _bin_or_text(s):
	if isinstance(s, unicode):
		return (True, s)
	for c in s:
		i = ord(c)
		if i < 0x20 or i >= 0x7f:
			return (False, s)
	return (True, s.decode("utf-8"))

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
		return "http-response"

	def export(self):
		out = dict()
		if self.code is not None:
			out["code"] = self.code
		if self.reason:
			out["reason"] = self.reason
		if self.headers:
			out["headers"] = self.headers
		if self.body:
			is_text, val = _bin_or_text(self.body)
			if is_text:
				out["body"] = val
			else:
				out["body-bin"] = b64encode(val)
		return out

class HttpStreamFormat(Format):
	def __init__(self, content):
		self.content = content

	def name(self):
		return "http-stream"

	def export(self):
		out = dict()
		is_text, val = _bin_or_text(self.content)
		if is_text:
			out["content"] = val
		else:
			out["content-bin"] = b64encode(val)
		return out

class GripPubControl(PubControl):
	def publish_http_response(self, channel, http_response, id=None, prev_id=None):
		if isinstance(http_response, basestring):
			http_response = HttpResponseFormat(body=http_response)
		item = Item(http_response, id, prev_id)
		super(GripPubControl, self).publish(channel, item)

	def publish_http_response_async(self, channel, http_response, id=None, prev_id=None, callback=None):
		if isinstance(http_response, basestring):
			http_response = HttpResponseFormat(body=http_response)
		item = Item(http_response, id, prev_id)
		super(GripPubControl, self).publish_async(channel, item, callback)

	def publish_http_stream(self, channel, http_stream, id=None, prev_id=None):
		if isinstance(http_stream, basestring):
			http_stream = HttpStreamFormat(http_stream)
		item = Item(http_stream, id, prev_id)
		super(GripPubControl, self).publish(channel, item)

	def publish_http_stream_async(self, channel, http_stream, id=None, prev_id=None, callback=None):
		if isinstance(http_stream, basestring):
			http_stream = HttpStreamFormat(http_stream)
		item = Item(http_stream, id, prev_id)
		super(GripPubControl, self).publish_async(channel, item, callback)

def create_hold(mode, channels, response):
	hold = dict()

	hold["mode"] = mode

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
		ichannel["name"] = c.name
		if c.prev_id:
			ichannel["prev-id"] = c.prev_id
		ichannels.append(ichannel)

	hold["channels"] = ichannels

	iresponse = None
	if response is not None:
		if isinstance(response, basestring):
			response = Response(body=response)

		iresponse = dict()
		if response.code is not None:
			iresponse["code"] = response.code
		if response.reason:
			iresponse["reason"] = response.reason
		if response.headers:
			iresponse["headers"] = response.headers
		if response.body:
			is_text, val = _bin_or_text(response.body)
			if is_text:
				iresponse["body"] = val
			else:
				iresponse["body-bin"] = b64encode(val)

	instruct = dict()
	instruct["hold"] = hold
	if iresponse:
		instruct["response"] = iresponse

	return json.dumps(instruct)

def create_hold_response(channels, response=None):
	return create_hold("response", channels, response)

def create_hold_stream(channels, response=None):
	return create_hold("stream", channels, response)

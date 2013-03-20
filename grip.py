from base64 import b64encode
import time
import json
import urllib2
import threading
import pickle
import jwt
import zmq

g_lock = threading.Lock()
g_ctx = zmq.Context()
g_control_uri = None
g_realm = None
g_secret = None
g_pubthread = None
g_pubsock = None

# returns (boolean is_text, string value)
def _bin_or_text(s):
	if isinstance(s, unicode):
		return (True, s)
	for c in s:
		i = ord(c)
		if i < 0x20 or i >= 0x7f:
			return (False, s)
	return (True, s.decode("utf-8"))

class Channel:
	def __init__(self, name, prev_id=None):
		self.name = name
		self.prev_id = prev_id

class Response:
	def __init__(self, code=None, reason=None, headers=None, body=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body

class Format:
	def name(self):
		pass

	def to_json(self):
		pass

class HttpResponseFormat(Format):
	def __init__(self, code=None, reason=None, headers=None, body=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body

	def name(self):
		return "http-response"

	def to_json(self):
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

	def to_json(self):
		out = dict()
		is_text, val = _bin_or_text(self.content)
		if is_text:
			out["content"] = val
		else:
			out["content-bin"] = b64encode(val)
		return out

class HttpRequestFormat(Format):
	def __init__(self, method=None, headers=None, body=None):
		self.method = method
		self.headers = headers
		self.body = body

	def name(self):
		return "http-request"

	def to_json(self):
		out = dict()
		if self.method:
			out["method"] = self.method
		if self.headers:
			out["headers"] = self.headers
		if self.body:
			is_text, val = _bin_or_text(self.body)
			if is_text:
				out["body"] = val
			else:
				out["body-bin"] = b64encode(val)
		return out

class XmppStanzaFormat(Format):
	def __init__(self, content):
		self.content = content

	def name(self):
		return "xmpp-stanza"

	def to_json(self):
		out = dict()
		out["content"] = self.content
		return out

class FppFormat(Format):
	def __init__(self, value):
		self.value = value

	def name(self):
		return "fpp"

	def to_json(self):
		return self.value

class Item:
	def __init__(self, formats, id=None, prev_id=None):
		self.id = id
		self.prev_id = prev_id
		if isinstance(formats, Format):
			formats = [formats]
		self.formats = formats

	def to_json(self):
		out = dict()
		if self.id:
			out["id"] = self.id
		if self.prev_id:
			out["prev-id"] = self.prev_id
		for f in self.formats:
			out[f.name()] = f.to_json()
		return out

def set_control_uri(uri):
	global g_control_uri

	g_lock.acquire()
	g_control_uri = uri
	g_lock.release()

def set_realm(s):
	global g_realm

	g_lock.acquire()
	g_realm = s
	g_lock.release()

def set_secret(s):
	global g_secret

	g_lock.acquire()
	g_secret = s
	g_lock.release()

def get_control_uri():
	g_lock.acquire()
	s = g_control_uri
	g_lock.release()
	return s

def get_realm():
	g_lock.acquire()
	s = g_realm
	g_lock.release()
	return s

def get_secret():
	g_lock.acquire()
	s = g_secret
	g_lock.release()
	return s

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

def _make_token(realm, secret):
	claim = dict()
	claim["iss"] = realm
	claim["exp"] = int(time.time()) + 600
	return jwt.encode(claim, secret)

def _pubcall(uri, realm, secret, channel, items_json):
	uri = uri + "/publish/" + channel + "/"

	headers = dict()
	if realm:
		headers["Authorization"] = "Bearer %s" % _make_token(realm, secret)
	headers["Content-Type"] = "application/json"

	content = dict()
	content["items"] = items_json
	content_raw = json.dumps(content)
	if isinstance(content_raw, unicode):
		content_raw = content_raw.encode("utf-8")

	try:
		urllib2.urlopen(urllib2.Request(uri, content_raw, headers))
	except Exception as e:
		print "warning: failed to publish: " + e.message

def _pubbatch(reqs):
	assert(len(reqs) > 0)
	uri = reqs[0][0]
	realm = reqs[0][1]
	secret = reqs[0][2]
	channel = reqs[0][3]
	items_json = list()
	for req in reqs:
		items_json.append(req[4])
	_pubcall(uri, realm, secret, channel, items_json)

def _pubworker(cond):
	sock = g_ctx.socket(zmq.SUB)
	sock.bind("inproc://publish")
	cond.acquire()
	cond.notify()
	cond.release()

	while True:
		# block until a request is ready, then read many if possible
		buf = sock.recv()
		reqs = list()
		reqs.append(pickle.loads(buf))
		for n in range(0, 99):
			try:
				buf = sock.recv(zmq.NOBLOCK)
			except zmq.ZMQError as e:
				if e.errno == zmq.EAGAIN:
					break
			reqs.append(pickle.loads(buf))

		# batch reqs by same realm/channel
		batch = list()
		for req in reqs:
			if len(batch) > 0:
				last = batch[-1]
				if req[0] != last[0] or req[1] != last[1] or req[2] != last[2] or req[3] != last[3]:
					_pubbatch(batch)
					batch = list()

			batch.append(req)

		if len(batch) > 0:
			_pubbatch(batch)

def _queue_publish(uri, realm, secret, channel, item):
	global g_pubthread
	global g_pubsock

	g_lock.acquire()
	if g_pubthread is None:
		c = threading.Condition()
		c.acquire()
		g_pubthread = threading.Thread(target=_pubworker, args=(c,))
		g_pubthread.daemon = True
		g_pubthread.start()
		c.wait()
		c.release()
		g_pubsock = g_ctx.socket(zmq.PUB)
		g_pubsock.connect("inproc://publish")
	g_lock.release()

	g_pubsock.send(pickle.dumps((uri, realm, secret, channel, item.to_json())))

def publish(channel, item, uri=None, realm=None, secret=None):
	if not uri:
		uri = get_control_uri()
		assert(uri)

	if not realm:
		realm = get_realm()

	if not secret:
		secret = get_secret()

	_queue_publish(uri, realm, secret, channel, item)

def publish_http_response(channel, http_response, id=None, prev_id=None):
	if isinstance(http_response, basestring):
		http_response = HttpResponseFormat(body=http_response)

	publish(channel, Item(http_response, id, prev_id))

def publish_http_stream(channel, http_stream, id=None, prev_id=None):
	if isinstance(http_stream, basestring):
		http_stream = HttpStreamFormat(http_stream)

	publish(channel, Item(http_stream, id, prev_id))

def publish_http_request(channel, http_request, id=None, prev_id=None):
	if isinstance(http_request, basestring):
		http_request = HttpRequestFormat(body=http_request)

	publish(channel, Item(http_request, id, prev_id))

def publish_xmpp_stanza(channel, xmpp_stanza, id=None, prev_id=None):
	if isinstance(xmpp_stanza, basestring):
		xmpp_stanza = XmppStanzaFormat(xmpp_stanza)

	publish(channel, Item(xmpp_stanza, id, prev_id))

def publish_fpp(channel, fpp, id=None, prev_id=None):
	if isinstance(fpp, basestring):
		fpp = FppFormat(fpp)

	publish(channel, Item(fpp, id, prev_id))

from copy import deepcopy
from struct import unpack
from .gripcontrol import is_python3, websocket_control_message
from .websocketevent import WebSocketEvent

class WebSocketContext(object):
	def __init__(self, id, meta, in_events, grip_prefix=''):
		self.id = id
		self.in_events = in_events
		self.read_index = 0
		self.accepted = False
		self.close_code = None
		self.closed = False
		self.out_close_code = None
		self.out_events = []
		self.orig_meta = meta
		self.meta = deepcopy(meta)
		self.grip_prefix = grip_prefix

	def is_opening(self):
		return (self.in_events and self.in_events[0].type == 'OPEN')

	def accept(self):
		self.accepted = True

	def close(self, code=None):
		self.closed = True
		if code is not None:
			self.out_close_code = code
		else:
			self.out_close_code = 0

	def can_recv(self):
		for n in range(self.read_index, len(self.in_events)):
			if self.in_events[n].type in ('TEXT', 'BINARY', 'CLOSE', 'DISCONNECT'):
				return True
		return False

	def recv(self):
		e = None
		while e is None and self.read_index < len(self.in_events):
			if self.in_events[self.read_index].type in ('TEXT', 'BINARY', 'CLOSE', 'DISCONNECT'):
				e = self.in_events[self.read_index]
			elif self.in_events[self.read_index].type == 'PING':
				self.out_events.append(WebSocketEvent('PONG'))
			self.read_index += 1
		if e is None:
			raise IndexError('read from empty buffer')

		if e.type == 'TEXT':
			if e.content:
				return e.content.decode('utf-8')
			else:
				if is_python3:
					return ''
				else:
					return u''
		elif e.type == 'BINARY':
			if e.content:
				return e.content
			else:
				if is_python3:
					return b''
				else:
					return ''
		elif e.type == 'CLOSE':
			if e.content and len(e.content) == 2:
				self.close_code = unpack('>H', e.content)[0]
			return None
		else: # DISCONNECT
			raise IOError('client disconnected unexpectedly')

	def send(self, message):
		if is_python3:
			if isinstance(message, str):
				message = message.encode('utf-8')
			content = b'm:' + message
		else:
			if isinstance(message, unicode):
				message = message.encode('utf-8')
			content = 'm:' + message
		self.out_events.append(WebSocketEvent('TEXT', content))

	def send_binary(self, message):
		if is_python3:
			if isinstance(message, str):
				message = message.encode('utf-8')
			content = b'm:' + message
		else:
			if isinstance(message, unicode):
				message = message.encode('utf-8')
			content = 'm:' + message
		self.out_events.append(WebSocketEvent('BINARY', content))

	def send_control(self, message):
		if is_python3:
			if isinstance(message, str):
				message = message.encode('utf-8')
			content = b'c:' + message
		else:
			if isinstance(message, unicode):
				message = message.encode('utf-8')
			content = 'c:' + message
		self.out_events.append(WebSocketEvent('TEXT', content))

	def subscribe(self, channel):
		self.send_control(websocket_control_message(
			'subscribe', {'channel': self.grip_prefix + channel}))

	def unsubscribe(self, channel):
		self.send_control(websocket_control_message(
			'unsubscribe', {'channel': self.grip_prefix + channel}))

	def detach(self):
		self.send_control(websocket_control_message('detach'))

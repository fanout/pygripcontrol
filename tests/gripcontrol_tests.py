import sys
import unittest
import json
import jwt
import calendar
from datetime import datetime
from struct import pack
from base64 import b64encode, b64decode
from pubcontrol import Item

is_python3 = sys.version_info >= (3,)

sys.path.append('../')
from src.gripcontrol import WebSocketEvent, Channel, Response, \
		parse_grip_uri, create_hold, validate_sig, create_grip_channel_header, \
		create_hold_response, create_hold_stream, decode_websocket_events, \
		encode_websocket_events, websocket_control_message, _parse_channels, \
		_get_hold_channels, _get_hold_response, _is_unicode_instance, \
		_is_basestring_instance, _bin_or_text, _timestamp_utcnow

class TestGripControl(unittest.TestCase):	 
	def test_create_hold(self):
		with self.assertRaises(AssertionError):
				create_hold('mode', [], 'response')
		hold = json.loads(create_hold('mode', 'channel', Response(
				'code', 'reason', 'headers', 'body')))
		self.assertFalse('timeout' in hold['hold'])
		self.assertEqual(hold['hold']['mode'], 'mode')
		self.assertEqual(hold['hold']['channels'], [{'name': 'channel'}])
		self.assertEqual(hold['response'], {'code': 'code',
				'reason': 'reason', 'headers': 'headers', 'body': 'body'})
		# Verify non-UTF8 data passed as the body is exported as content-bin
		hold = json.loads(create_hold('mode', 'channel', Response(
				'code', 'reason', 'headers', pack('hhh', 253, 254, 255))))
		self.assertEqual(hold['hold']['mode'], 'mode')
		self.assertEqual(hold['response'], json.loads(json.dumps({'code': 'code',
				'reason': 'reason', 'headers': 'headers', 'body-bin':
				b64encode(pack('hhh', 253, 254, 255)).decode('utf-8')})))
		hold = json.loads(create_hold('mode', 'channel', None))
		self.assertEqual(hold['hold']['mode'], 'mode')
		self.assertEqual('response' in hold, False)
		hold = json.loads(create_hold('mode', 'channel', None, 'timeout'))
		self.assertEqual(hold['hold']['mode'], 'mode')
		self.assertEqual(hold['hold']['timeout'], 'timeout')

	def test_parse_grip_uri(self):
		uri = 'http://api.fanout.io/realm/realm?iss=realm' + '&key=base64:geag121321=='
		config = parse_grip_uri(uri)
		self.assertEqual(config['control_uri'], 'http://api.fanout.io/realm/realm')
		self.assertEqual(config['control_iss'], 'realm')
		self.assertEqual(config['key'], b64decode('geag121321=='))
		uri = 'https://api.fanout.io/realm/realm?iss=realm' + '&key=base64:geag121321=='
		config = parse_grip_uri(uri)
		self.assertEqual(config['control_uri'], 'https://api.fanout.io/realm/realm')
		config = parse_grip_uri('http://api.fanout.io/realm/realm')
		self.assertEqual(config['control_uri'], 'http://api.fanout.io/realm/realm')
		self.assertEqual('control_iss' in config, False)
		self.assertEqual('key' in config, False)
		uri = 'http://api.fanout.io/realm/realm?iss=realm' + \
                '&key=base64:geag121321==&param1=value1&param2=value2'
		config = parse_grip_uri(uri)
		try:
			self.assertEqual(config['control_uri'], 'http://api.fanout.io/realm/realm?' +
					'param1=value1&param2=value2')
		except:
			self.assertEqual(config['control_uri'], 'http://api.fanout.io/realm/realm?' +
					'param2=value2&param1=value1')            
		self.assertEqual(config['control_iss'], 'realm')
		self.assertEqual(config['key'], b64decode('geag121321=='))
		config = parse_grip_uri('http://api.fanout.io:8080/realm/realm/')
		self.assertEqual(config['control_uri'], 'http://api.fanout.io:8080/realm/realm')
		uri = 'http://api.fanout.io/realm/realm?iss=realm' + '&key=geag121321=='
		config = parse_grip_uri(uri)
		self.assertEqual(config['key'], 'geag121321==')

	def test_validate_sig(self):
		token = jwt.encode({'iss': 'realm', 'exp': 
                calendar.timegm(datetime.utcnow().utctimetuple()) + 3600},
				'key')
		self.assertTrue(validate_sig(token, 'key'))
		token = jwt.encode({'iss': 'realm', 'exp':
                calendar.timegm(datetime.utcnow().utctimetuple()) - 3600},
				'key')
		self.assertEqual(validate_sig(token, 'key'), False) 
		token = jwt.encode({'iss': 'realm', 'exp': 
                calendar.timegm(datetime.utcnow().utctimetuple()) + 3600},
				'key')
		self.assertEqual(validate_sig(token, 'wrong_key'), False) 

	def test_create_grip_channel_header(self):
		with self.assertRaises(AssertionError):
			create_grip_channel_header([])
		header = create_grip_channel_header('channel')
		self.assertEqual(header, 'channel')
		header = create_grip_channel_header(Channel('channel'))
		self.assertEqual(header, 'channel')
		header = create_grip_channel_header(Channel('channel',
				'prev-id'))
		self.assertEqual(header, 'channel; prev-id=prev-id')
		header = create_grip_channel_header([Channel('channel1',
				'prev-id1'), Channel('channel2', 'prev-id2')])
		self.assertEqual(header, 'channel1; prev-id=prev-id1, channel2; prev-id=prev-id2')

	def test_create_hold_response(self):
		hold = json.loads(create_hold_response('channel', Response(
				'code', 'reason', 'headers', 'body')))
		self.assertEqual(hold['hold']['mode'], 'response')
		self.assertEqual('timeout' in hold['hold'], False)
		self.assertEqual(hold['hold']['channels'], [{'name': 'channel'}])
		self.assertEqual(hold['response'], {'code': 'code',
				'reason': 'reason', 'headers': 'headers', 'body': 'body'})
		hold = json.loads(create_hold_response('channel', None, 'timeout'))
		self.assertEqual('response' in hold, False)
		self.assertEqual(hold['hold']['mode'], 'response')
		self.assertEqual(hold['hold']['timeout'], 'timeout')

	def test_create_hold_stream(self):
		hold = json.loads(create_hold_stream('channel', Response(
				'code', 'reason', 'headers', 'body')))
		self.assertEqual(hold['hold']['mode'], 'stream')
		self.assertEqual('timeout' in hold['hold'], False)
		self.assertEqual(hold['hold']['channels'], [{'name': 'channel'}])
		self.assertEqual(hold['response'], {'code': 'code',
				'reason': 'reason', 'headers': 'headers', 'body': 'body'})
		hold = json.loads(create_hold_stream('channel', None))
		self.assertEqual('response' in hold, False)
		self.assertEqual(hold['hold']['mode'], 'stream')

	def test_decode_websocket_events(self):
		if is_python3:
			events = decode_websocket_events(b"OPEN\r\nTEXT 5\r\nHello" + 
					b"\r\nTEXT 0\r\n\r\nCLOSE\r\nTEXT\r\nCLOSE\r\n")
		else:
			events = decode_websocket_events("OPEN\r\nTEXT 5\r\nHello" + 
					"\r\nTEXT 0\r\n\r\nCLOSE\r\nTEXT\r\nCLOSE\r\n")
		self.assertEqual(len(events), 6)
		self.assertEqual(events[0].type, 'OPEN')
		self.assertEqual(events[0].content, None)
		self.assertEqual(events[1].type, 'TEXT')
		if is_python3:
			self.assertEqual(events[1].content, b'Hello')
		else:
			self.assertEqual(events[1].content, 'Hello')
		self.assertEqual(events[2].type, 'TEXT')
		if is_python3:
			self.assertEqual(events[2].content, b'')
		else:
			self.assertEqual(events[2].content, '')
		self.assertEqual(events[3].type, 'CLOSE')
		self.assertEqual(events[3].content, None)
		self.assertEqual(events[4].type, 'TEXT')
		self.assertEqual(events[4].content, None)
		self.assertEqual(events[5].type, 'CLOSE')
		self.assertEqual(events[5].content, None)
		if is_python3:
			events = decode_websocket_events(b"OPEN\r\n")
		else:
			events = decode_websocket_events("OPEN\r\n")
		self.assertEqual(len(events), 1)
		self.assertEqual(events[0].type, 'OPEN')
		self.assertEqual(events[0].content, None)
		if is_python3:
			events = decode_websocket_events(b"TEXT 5\r\nHello\r\n")
		else:
			events = decode_websocket_events("TEXT 5\r\nHello\r\n")
		self.assertEqual(len(events), 1)
		self.assertEqual(events[0].type, 'TEXT')
		if is_python3:
			self.assertEqual(events[0].content, b'Hello')
		else:
			self.assertEqual(events[0].content, 'Hello')
		with self.assertRaises(ValueError):
			decode_websocket_events("TEXT 5")
		with self.assertRaises(ValueError):
			decode_websocket_events("OPEN\r\nTEXT")

	def test_encode_websocket_events(self):
		events = encode_websocket_events([
				WebSocketEvent("TEXT", "Hello"), 
				WebSocketEvent("TEXT", ""),
				WebSocketEvent("TEXT", None)])
		if is_python3:
			self.assertEqual(events, b"TEXT 5\r\nHello\r\nTEXT 0\r\n\r\nTEXT\r\n")
		else:
			self.assertEqual(events, "TEXT 5\r\nHello\r\nTEXT 0\r\n\r\nTEXT\r\n")
		events = encode_websocket_events([WebSocketEvent("OPEN")])
		if is_python3:
			self.assertEqual(events, b"OPEN\r\n")
		else:
			self.assertEqual(events, "OPEN\r\n")

	def test_websocket_control_message(self):
		message = websocket_control_message('type')
		self.assertEqual(message, '{"type": "type"}')
		message = json.loads(websocket_control_message('type', {'arg1': 'val1',
				'arg2': 'val2'}))
		self.assertEqual(message['type'], 'type')
		self.assertEqual(message['arg1'], 'val1')
		self.assertEqual(message['arg2'], 'val2')

	def test_parse_channels(self):
		channels = _parse_channels('channel')
		self.assertEqual(channels[0].name, 'channel')
		self.assertEqual(channels[0].prev_id, None)
		channels = _parse_channels(Channel('channel'))
		self.assertEqual(channels[0].name, 'channel')
		self.assertEqual(channels[0].prev_id, None)
		channels = _parse_channels(Channel('channel', 'prev-id'))
		self.assertEqual(channels[0].name, 'channel')
		self.assertEqual(channels[0].prev_id, 'prev-id')
		channels = _parse_channels([Channel('channel1', 'prev-id'),
				Channel('channel2')])
		self.assertEqual(channels[0].name, 'channel1')
		self.assertEqual(channels[0].prev_id, 'prev-id')
		self.assertEqual(channels[1].name, 'channel2')
		self.assertEqual(channels[1].prev_id, None)
		with self.assertRaises(AssertionError):
			_parse_channels([])

	def test_get_hold_channels(self):
		hold_channels = _get_hold_channels([Channel('channel')])
		self.assertEqual(hold_channels[0], {'name': 'channel'})
		hold_channels = _get_hold_channels([
				Channel('channel', 'prev-id')])
		self.assertEqual(hold_channels[0], {'name': 'channel', 'prev-id':
				'prev-id'})
		hold_channels = _get_hold_channels([
				Channel('channel1', 'prev-id1'), Channel('channel2', 'prev-id2')])
		self.assertEqual(hold_channels[0], {'name': 'channel1', 'prev-id':
				'prev-id1'})
		self.assertEqual(hold_channels[1], {'name': 'channel2', 'prev-id':
				'prev-id2'})

	def test_get_hold_response(self):
		response = _get_hold_response(None)
		self.assertEqual(response, None)
		response = _get_hold_response('body')
		self.assertEqual(response['body'], 'body')
		self.assertEqual('code' in response, False)
		self.assertEqual('reason' in response, False)
		self.assertEqual('headers' in response, False)
		# Verify non-UTF8 data passed as the body is exported as content-bin
		response = _get_hold_response(pack('hhh', 253, 254, 255))
		self.assertEqual(response['body-bin'], b64encode(
                pack('hhh', 253, 254, 255)).decode('utf-8'))
		response = _get_hold_response(Response('code', 'reason',
				{'header1': 'val1'}, "body\u2713"))
		self.assertEqual(response['code'], 'code')
		self.assertEqual(response['reason'], 'reason')
		self.assertEqual(response['headers'], {'header1': 'val1'})
		self.assertEqual(response['body'], "body\u2713")
		response = _get_hold_response(Response(None, None, {}, None))
		self.assertEqual('code' in response, False)
		self.assertEqual('body' in response, False)
		self.assertEqual('reason' in response, False)
		self.assertEqual('headers' in response, False)

	def test_is_unicode_instance(self):
		self.assertTrue(_is_unicode_instance(u'hello'))
		self.assertFalse(_is_unicode_instance('hello'.encode('ascii')))

	def test_is_basestring_instance(self):
		self.assertTrue(_is_basestring_instance(u'hello'))
		self.assertTrue(_is_basestring_instance('hello'))

	def test_bin_or_text(self):
		self.assertEqual(_bin_or_text('hello'), (True, 'hello'))
		self.assertEqual(_bin_or_text(pack('hhh', 253, 254, 255)),
				(False, pack('hhh', 253, 254, 255)))

	def test_timestamp_utcnow(self):
		self.assertEqual(_timestamp_utcnow(), 
				calendar.timegm(datetime.utcnow().utctimetuple()))

if __name__ == '__main__':
		unittest.main()

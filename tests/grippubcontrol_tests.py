import sys
import unittest
from base64 import b64encode
from pubcontrol import Item

sys.path.append('../')
from src.grippubcontrol import GripPubControl
from src.httpresponseformat import HttpResponseFormat
from src.httpstreamformat import HttpStreamFormat

class GripPubControlTestClass(GripPubControl):
	def __init__(self):
		super(GripPubControl, self).__init__()
		self.was_finish_called = False
		self.publish_channel = None
		self.publish_item = None
		self.publish_callback = None

	def finish(self):
		self.was_finish_called = True

	def publish(self, channel, item, blocking=False, callback=None):
		self.publish_channel = channel
		self.publish_blocking = blocking
		self.publish_item = item
		self.publish_callback = callback

class TestGripPubControl(unittest.TestCase):
	def test_initialize(self):
		pc = GripPubControl()
		self.assertEqual(len(pc.clients), 0)
		config = {'control_uri': 'uri', 'control_iss': 'iss', 'key': 'key'}
		pc = GripPubControl(config)
		self.assertEqual(len(pc.clients), 1)
		config = [{'control_uri': 'uri', 'control_iss': 'iss', 'key': 'key'},
				{'control_uri': 'uri', 'control_iss': 'iss', 'key': 'key'}]
		pc = GripPubControl(config)
		self.assertEqual(len(pc.clients), 2)

	def test_apply_grip_config(self):
		pc = GripPubControl()
		config = {'control_uri': 'uri'}
		pc.apply_grip_config(config)
		self.assertEqual(pc.clients[0].uri, 'uri')
		pc = GripPubControl()
		config = [{'control_uri': 'uri'},
				{'control_uri': 'uri1', 'control_iss': 'iss1', 'key': 'key1'},
				{'control_uri': 'uri2', 'control_iss': 'iss2', 'key': 'key2'}]
		pc.apply_grip_config(config)
		self.assertEqual(pc.clients[0].uri, 'uri')
		self.assertEqual(pc.clients[0].auth_jwt_claim, None)
		self.assertEqual(pc.clients[0].auth_jwt_key, None)
		self.assertEqual(pc.clients[1].uri, 'uri1')
		self.assertEqual(pc.clients[1].auth_jwt_claim,
				{'iss': 'iss1'})
		self.assertEqual(pc.clients[1].auth_jwt_key, 'key1')
		self.assertEqual(pc.clients[2].uri, 'uri2')
		self.assertEqual(pc.clients[2].auth_jwt_claim,
				{'iss': 'iss2'})
		self.assertEqual(pc.clients[2].auth_jwt_key, 'key2')

	def test_publish_http_response_string(self):
		pc = GripPubControlTestClass()
		pc.publish_http_response('channel', 'item', 'id', None, True)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, True)
		self.assertEqual(pc.publish_item.export(),
				Item(HttpResponseFormat(None, None, None, 'item'), 'id').export())

	def test_publish_http_response_httpresponseformat(self):
		pc = GripPubControlTestClass()
		pc.publish_http_response('channel', HttpResponseFormat('code',
				'reason', 'headers', 'body'), 'id', 'prev-id')
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, False)
		self.assertEqual(pc.publish_item.export(), Item(HttpResponseFormat(
				'code', 'reason', 'headers', 'body'), 'id', 'prev-id').export())

	def callback_for_testing(self, result, error):
		self.assertEqual(self.has_callback_been_called, False)
		self.assertEqual(result, False)
		self.assertEqual(error, 'error')
		self.has_callback_been_called = True

	def test_publish_http_response_with_callback_string(self):
		self.has_callback_been_called = False
		pc = GripPubControlTestClass()
		pc.publish_http_response('channel', HttpResponseFormat('code',
				'reason', 'headers', 'body'), 'id', 'prev-id', False,
				self.callback_for_testing)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, False)
		self.assertEqual(pc.publish_item.export(), Item(HttpResponseFormat(
				'code', 'reason', 'headers', 'body'), 'id', 'prev-id').export())
		pc.publish_callback(False, 'error')
		self.assertTrue(self.has_callback_been_called)

	def test_publish_http_response_with_callback_format(self):
		self.has_callback_been_called = False
		pc = GripPubControlTestClass()
		pc.publish_http_response('channel', HttpResponseFormat('code',
				'reason', 'headers', 'body'), None, None, False, 
				self.callback_for_testing)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_item.export(), Item(HttpResponseFormat(
				'code', 'reason', 'headers', 'body')).export())
		pc.publish_callback(False, 'error')
		self.assertTrue(self.has_callback_been_called)

	def test_publish_http_stream_string(self):
		pc = GripPubControlTestClass()
		pc.publish_http_stream('channel', 'item', None, 'prev-id')
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, False)
		self.assertEqual(pc.publish_item.export(), Item(HttpStreamFormat(
				'item'), None, 'prev-id').export())

	def test_publish_http_stream_httpstreamformat(self):
		pc = GripPubControlTestClass()
		pc.publish_http_stream('channel', HttpStreamFormat(None, True), None, None, True)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, True)
		self.assertEqual(pc.publish_item.export(), Item(HttpStreamFormat(
				None, True)).export())

	def test_publish_http_stream_with_callback_string(self):
		self.has_callback_been_called = False
		pc = GripPubControlTestClass()
		pc.publish_http_stream('channel', 'item', None, 'prev-id', False,
				self.callback_for_testing)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_blocking, False)
		self.assertEqual(pc.publish_item.export(), Item(HttpStreamFormat(
				'item'), None, 'prev-id').export())
		pc.publish_callback(False, 'error')
		self.assertTrue(self.has_callback_been_called)

	def test_publish_http_stream_with_callback_format(self):
		self.has_callback_been_called = False
		pc = GripPubControlTestClass()
		pc.publish_http_stream('channel', HttpStreamFormat(None, True),
				None, None, False, self.callback_for_testing)
		self.assertEqual(pc.publish_channel, 'channel')
		self.assertEqual(pc.publish_item.export(), Item(HttpStreamFormat(
				None, True)).export())
		pc.publish_callback(False, 'error')
		self.assertTrue(self.has_callback_been_called)

if __name__ == '__main__':
		unittest.main()

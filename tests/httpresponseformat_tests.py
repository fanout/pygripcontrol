import sys
import unittest
from base64 import b64encode
from struct import pack

sys.path.append('../')
from src.httpresponseformat import HttpResponseFormat

class TestHttpResponseFormat(unittest.TestCase):
	def test_initialize(self):
		format = HttpResponseFormat()
		self.assertEqual(format.code, None)
		self.assertEqual(format.reason, None)
		self.assertEqual(format.headers, None)
		self.assertEqual(format.body, None)
		format = HttpResponseFormat('code', 'reason', 'headers', 'body')
		self.assertEqual(format.code, 'code')
		self.assertEqual(format.reason, 'reason')
		self.assertEqual(format.headers, 'headers')
		self.assertEqual(format.body, 'body')

	def test_name(self):
		format = HttpResponseFormat()
		self.assertEqual(format.name(), 'http-response')

	def test_export(self):
		format = HttpResponseFormat()
		self.assertEqual(format.export(), {})
		format = HttpResponseFormat('code', 'reason', 'headers', "body")
		self.assertEqual(format.export(), {'code': 'code', 'reason': 'reason',
				'headers': 'headers', 'body': "body"})
		# Verify non-UTF8 data passed as the body is exported as body-bin
		format = HttpResponseFormat('code', 'reason', 'headers',
				pack('hhh', 253, 254, 255))
		self.assertEqual(format.export(), {'code': 'code', 'reason': 'reason',
				'headers': 'headers', 'body-bin': b64encode(
                pack('hhh', 253, 254, 255))})

if __name__ == '__main__':
		unittest.main()

import sys
import unittest
from base64 import b64encode
from struct import pack

sys.path.append('../')
from src.httpstreamformat import HttpStreamFormat

class TestHttpStreamFormat(unittest.TestCase):
	def test_initialize(self):
		format = HttpStreamFormat('content')
		self.assertEqual(format.content, 'content')
		self.assertEqual(format.close, False)
		format = HttpStreamFormat(None, True)
		self.assertEqual(format.content, None)
		self.assertEqual(format.close, True)
		was_exception_raised = False
		try:
			HttpStreamFormat()				
		except:
			was_exception_raised = True
		self.assertTrue(was_exception_raised)

	def test_name(self):
		format = HttpStreamFormat('content')
		self.assertEqual(format.name(), 'http-stream')

	def test_export(self):
		format = HttpStreamFormat(None, True)
		self.assertEqual(format.export(), {'action': 'close'})
		format = HttpStreamFormat("body")
		self.assertEqual(format.export(), {'content': "body"})
		# Verify non-UTF8 data passed as the body is exported as content-bin
		format = HttpStreamFormat(pack('hhh', 253, 254, 255))
		self.assertEqual(format.export(), {'content-bin': b64encode(
				pack('hhh', 253, 254, 255))})

if __name__ == '__main__':
		unittest.main()

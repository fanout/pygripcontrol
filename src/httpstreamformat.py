#    httpstreamformat.py
#    ~~~~~~~~~
#    This module implements the HttpStreamFormat class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

from base64 import b64encode
from pubcontrol import Format
from .gripcontrol import _bin_or_text

# The HttpStreamFormat class is the format used to publish messages to
# HTTP stream clients connected to a GRIP proxy.
class HttpStreamFormat(Format):

	# Initialize with either the message content or a boolean indicating that
	# the streaming connection should be closed. If neither the content nor
	# the boolean flag is set then an error will be raised.
	def __init__(self, content=None, close=False, content_filters=None):
		self.content = content
		self.close = close
		self.content_filters = content_filters
		if not self.close and self.content is None:
			raise ValueError('content not set')

	# The name used when publishing this format.
	def name(self):
		return 'http-stream'

	# Exports the message in the required format depending on whether the
	# message content is binary or not, or whether the connection should
	# be closed.
	def export(self):
		out = dict()
		if self.close:
			out['action'] = 'close'
		else:
			if self.content_filters is not None:
				out['content-filters'] = self.content_filters

			is_text, val = _bin_or_text(self.content)
			if is_text:
				out['content'] = val
			else:
				out['content-bin'] = b64encode(val)
		return out

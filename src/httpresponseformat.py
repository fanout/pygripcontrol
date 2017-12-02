#    httpresponseformat.py
#    ~~~~~~~~~
#    This module implements the HttpResponseFormat class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

from base64 import b64encode
from pubcontrol import Format
from .gripcontrol import _bin_or_text

# The HttpResponseFormat class is the format used to publish messages to
# HTTP response clients connected to a GRIP proxy.
class HttpResponseFormat(Format):

	# Initialize with the message code, reason, headers, and body to send
	# to the client when the message is published.
	def __init__(self, code=None, reason=None, headers=None, body=None, content_filters=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body
		self.content_filters = content_filters

	# The name used when publishing this format.
	def name(self):
		return 'http-response'

	# Export the message into the required format and include only the fields
	# that are set. The body is exported as base64 if the text is encoded as
	# binary.
	def export(self):
		out = dict()
		if self.content_filters is not None:
			out['content-filters'] = self.content_filters
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

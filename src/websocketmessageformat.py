#    websocketmessageformat.py
#    ~~~~~~~~~
#    This module implements the WebSocketMessageFormat class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

from base64 import b64encode
from pubcontrol import Format
from .gripcontrol import _is_unicode_instance

# The WebSocketMessageFormat class is the format used to publish data to
# WebSocket clients connected to GRIP proxies.
class WebSocketMessageFormat(Format):

	# Initialize with the message content and a flag indicating whether the
	# message content should be sent as base64-encoded binary data.
	def __init__(self, content, binary=False):
		self.content = content
		self.binary = binary

	# The name used when publishing this format.
	def name(self):
		return 'ws-message'

	# Exports the message in the required format depending on whether the
	# message content is binary or not.
	def export(self):
		out = dict()
		val = self.content
		if self.binary:
			if _is_unicode_instance(val):
				val = val.encode('utf-8')
			out['content-bin'] = b64encode(val)
		else:
			if not _is_unicode_instance(val):
				val = val.decode('utf-8')
			out['content'] = val
		return out

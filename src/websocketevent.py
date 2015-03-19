#    websocketevent.py
#    ~~~~~~~~~
#    This module implements the WebSocketEvent class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

# The WebSocketEvent class represents WebSocket event information that is
# used with the GRIP WebSocket-over-HTTP protocol. It includes information
# about the type of event as well as an optional content field.
class WebSocketEvent(object):

	# Initialize with a specified event type and optional content information.
	def __init__(self, type, content=None):
		self.type = type
		self.content = content


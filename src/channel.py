#    channel.py
#    ~~~~~~~~~
#    This module implements the Channel class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

# The Channel class is used to represent a channel in a GRIP proxy and
# tracks the previous ID of the last message.
class Channel(object):

	# Initialize with the channel name and an optional previous ID.
	def __init__(self, name, prev_id=None):
		self.name = name
		self.prev_id = prev_id

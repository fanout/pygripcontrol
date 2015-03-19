#    response.py
#    ~~~~~~~~~
#    This module implements the Response class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

# The Response class is used to represent a set of HTTP response data.
# Populated instances of this class are serialized to JSON and passed
# to the GRIP proxy in the body. The GRIP proxy then parses the message
# and deserialized the JSON into an HTTP response that is passed back 
# to the client.
class Response(object):

	# Initialize with an HTTP response code, reason, headers, and body.
	def __init__(self, code=None, reason=None, headers=None, body=None):
		self.code = code
		self.reason = reason
		self.headers = headers
		self.body = body



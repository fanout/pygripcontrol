#    grippubcontrol.py
#    ~~~~~~~~~
#    This module implements the GripPubControl class.
#    :authors: Justin Karneges, Konstantin Bokarius.
#    :copyright: (c) 2015 by Fanout, Inc.
#    :license: MIT, see LICENSE for more details.

from pubcontrol import PubControl, Item
from .httpresponseformat import HttpResponseFormat
from .httpstreamformat import HttpStreamFormat
from .gripcontrol import _is_basestring_instance
import six

# The GripPubControl class allows consumers to easily publish HTTP response
# and HTTP stream format messages to GRIP proxies. Configuring GripPubControl
# is slightly different from configuring PubControl in that the 'uri' and
# 'iss' keys in each config entry should have a 'control_' prefix.
# GripPubControl inherits from PubControl and therefore also provides all
# of the same functionality.
class GripPubControl(PubControl):

	# Initialize with or without a configuration. A configuration can be applied
	# after initialization via the apply_grip_config method. Optionally specify
	# a subscription callback method that will be executed whenever a channel is 
	# subscribed to or unsubscribed from. The callback accepts two parameters:
	# the first parameter a string containing 'sub' or 'unsub' and the second
	# parameter containing the channel name. Optionally specify a ZMQ context
	# to use otherwise the global ZMQ context will be used.
	def __init__(self, config=None, sub_callback=None, zmq_context=None):
		super(GripPubControl, self).__init__(None, sub_callback, zmq_context)
		self.clients = list()
		if config:
			self.apply_grip_config(config)

	# Apply the specified configuration to this GripPubControl instance. The
	# configuration object can either be a hash or an array of hashes where
	# each hash corresponds to a single PubControlClient instance. Each hash
	# will be parsed and a PubControlClient will be created either using just
	# a URI or a URI and JWT authentication information.
	def apply_grip_config(self, config):
		if not isinstance(config, list):
			config = [config]
		for entry in config:
			pc_config = {}
			if 'control_uri' in entry:
				pc_config['uri'] = entry['control_uri']
				if 'control_iss' in entry:
					pc_config['iss'] = entry['control_iss']
				if 'key' in entry:
					pc_config['key'] = entry['key']
			elif 'control_zmq_uri' in entry:
				pc_config['zmq_uri'] = entry['control_zmq_uri']
			if entry.get('require_subscribers'):
				pc_config['require_subscribers'] = True
			self.apply_config(pc_config)

	# Publish an HTTP response format message to all of the configured
	# PubControlClients with a specified channel, message, and optional
	# ID, previous ID, and callback. Note that the 'http_response' parameter
	# can be provided as either an HttpResponseFormat instance or a string
	# (in which case an HttpResponseFormat instance will automatically be
	# created and have the 'body' field set to the specified string). The
	# blocking parameter indicates whether the call should be blocking or
	# non-blocking. When specified, the callback method will be called after
	# publishing is complete and passed a result and error message (if an
	# error was encountered).
	def publish_http_response(self, channel, http_response, id=None, prev_id=None, blocking=False, callback=None):
		if _is_basestring_instance(http_response):
			http_response = HttpResponseFormat(body=http_response)
		item = Item(http_response, id, prev_id)
		self.publish(channel, item, blocking=blocking, callback=callback)

	# Publish an HTTP stream format message to all of the configured
	# PubControlClients with a specified channel, message, and optional
	# ID, previous ID, and callback. Note that the 'http_stream' parameter
	# can be provided as either an HttpStreamFormat instance or a string
	# (in which case an HttpStreamFormat instance will automatically be
	# created and have the 'content' field set to the specified string). The
	# blocking parameter indicates whether the call should be blocking or
	# non-blocking. When specified, the callback method will be called after
	# publishing is complete and passed a result and error message (if an
	# error was encountered).
	def publish_http_stream(self, channel, http_stream, id=None, prev_id=None, blocking=False, callback=None):
		if _is_basestring_instance(http_stream):
			http_stream = HttpStreamFormat(http_stream)
		item = Item(http_stream, id, prev_id)
		self.publish(channel, item, blocking=blocking, callback=callback)

	# Update the origin server settings for the GRIP proxy. To set a non-SSL
	# target, set 'host' and 'port'. To set an SSL target, set 'ssl_host' and
	# 'ssl_port'. For a target to be accepted, both its host and port must be
	# specified in this call. For services that support more than one input
	# routing domain, 'route_domain' can be used to select the domain to
	# apply the changes to. The call will be made against all configured
	# PubControlClients. If any of the lower level calls fail, this method
	# will raise an exception.
	def set_origin(self, route_domain=None, host=None, port=None, ssl_host=None, ssl_port=None, rewrite_host=True, over_http=True):
		params = {}
		if host is not None:
			params['host'] = host
		if port is not None:
			params['port'] = str(port)
		if ssl_host is not None:
			params['ssl_host'] = ssl_host
		if ssl_port is not None:
			params['ssl_port'] = str(ssl_port)
		if rewrite_host is not None:
			params['rewrite_host'] = 'true' if rewrite_host else 'false'
		if over_http is not None:
			params['over_http'] = 'true' if over_http else 'false'

		if not route_domain:
			route_domain = 'default'

		ret = self.http_call('/http/%s/' % route_domain, params)
		for client, result in six.iteritems(ret):
			if len(result) == 1:
				e = result[0]
				raise ValueError('failed to set origin for service %s: %s' % (client.uri, e.message))

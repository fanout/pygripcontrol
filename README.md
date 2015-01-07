PyGripControl
=============
Author: Justin Karneges <justin@fanout.io>

GRIP library for Python.

Requirements
------------

* jwt
* pubcontrol

Install
-------

You can install from PyPi:

    sudo pip install gripcontrol

Or from this repository:

    sudo python setup.py install

Sample usage
------------

Long-polling instruction using Django:

```python
from gripcontrol import create_grip_channel_header

def handler(request):
    resp = HttpResponse('no data\n')
    resp['Grip-Hold'] = 'response'
    resp['Grip-Channel'] = create_grip_channel_header('mychannel')
    return resp
```

Publishing:

```python
from base64 import b64decode
from gripcontrol import GripPubControl

pub = GripPubControl({
    'uri': 'https://api.fanout.io/realm/myrealm',
    'iss': 'myrealm',
    'key': b64decode('myrealmkey')
})
pub.publish_http_response('mychannel', 'some data\n')
```

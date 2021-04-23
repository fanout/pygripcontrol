#!/usr/bin/env python

from setuptools import setup

setup(
name='gripcontrol',
version='4.1.0',
description='GRIP library',
author='Justin Karneges',
author_email='justin@fanout.io',
url='https://github.com/fanout/pygripcontrol',
license='MIT',
package_dir={'gripcontrol': 'src'},
packages=['gripcontrol'],
install_requires=['PyJWT>=1.5,<3', 'pubcontrol>=3.0,<4', 'six>=1.10.0,<2'],
classifiers=[
	'Topic :: Utilities',
	'License :: OSI Approved :: MIT License'
]
)

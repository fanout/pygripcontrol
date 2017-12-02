#!/usr/bin/env python

from setuptools import setup

setup(
name='gripcontrol',
version='3.2.0',
description='GRIP library',
author='Justin Karneges',
author_email='justin@fanout.io',
url='https://github.com/fanout/pygripcontrol',
license='MIT',
package_dir={'gripcontrol': 'src'},
packages=['gripcontrol'],
install_requires=['PyJWT>=1.5,<2', 'pubcontrol>=2.4.1,<3', 'six>=1.10.0,<2'],
classifiers=[
	'Topic :: Utilities',
	'License :: OSI Approved :: MIT License'
]
)

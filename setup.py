#!/usr/bin/env python

from setuptools import setup

setup(
name="gripcontrol",
version="2.3.2",
description="GRIP library",
author="Justin Karneges",
author_email="justin@affinix.com",
url="https://github.com/fanout/pygripcontrol",
license="MIT",
package_dir={'gripcontrol': 'src'},
packages=['gripcontrol'],
install_requires=["PyJWT>=0,<1", "pubcontrol>=2,<3"],
classifiers=[
	"Topic :: Utilities",
	"License :: OSI Approved :: MIT License"
]
)

#!/usr/bin/env python

from setuptools import setup

setup(
name="gripcontrol",
version="1.0.4",
description="GRIP library",
author="Justin Karneges",
author_email="justin@affinix.com",
url="https://github.com/fanout/pygripcontrol",
license="MIT",
py_modules=["gripcontrol"],
install_requires=["PyJWT>=0.1.6", "pubcontrol>=1.0.4"],
classifiers=[
	"Topic :: Utilities",
	"License :: OSI Approved :: MIT License"
]
)

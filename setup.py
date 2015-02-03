#!/usr/bin/env python

from setuptools import setup

setup(
name="gripcontrol",
version="2.2.1",
description="GRIP library",
author="Justin Karneges",
author_email="justin@affinix.com",
url="https://github.com/fanout/pygripcontrol",
license="MIT",
py_modules=["gripcontrol"],
install_requires=["PyJWT>=0,<1", "pubcontrol>=2,<3"],
classifiers=[
	"Topic :: Utilities",
	"License :: OSI Approved :: MIT License"
]
)

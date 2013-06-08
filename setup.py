#!/usr/bin/env python

from setuptools import setup

setup(
name="gripcontrol",
version="1.0.2",
description="GRIP library",
author="Justin Karneges",
author_email="justin@affinix.com",
url="https://github.com/fanout/pygripcontrol",
license="MIT",
py_modules=["gripcontrol"],
install_requires=["pubcontrol==1.0.2"],
classifiers=[
	"Topic :: Utilities",
	"License :: OSI Approved :: MIT License"
]
)

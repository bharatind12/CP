#!/usr/bin/env python3

import os
import ssl

from setuptools import setup

# Ignore ssl if it fails
if not os.environ.get("PYTHONHTTPSVERIFY", "") and getattr(ssl, "_create_unverified_context", None):
    ssl._create_default_https_context = ssl._create_unverified_context

setup(
    name="cone-penetrometer",
    version="0.1.0",
    description="IXAR Robotics Solutions",
    license="MIT",
    install_requires=[
        "appdirs == 1.4.4",
        "fastapi == 0.63.0",
        "fastapi-versioning == 0.9.1",
        "loguru == 0.5.3",
        "uvicorn == 0.13.4",
        "starlette==0.13.6",
        "aiofiles==0.8.0",
    ],
)
# -*- coding: utf-8 -*-
"""'Externally' adjustable config vars."""

from os import environ

# TODO: validation is a good idea.

# Default HTTPS port by default.
PORT = int(environ['PORT']) if 'PORT' in environ else 443

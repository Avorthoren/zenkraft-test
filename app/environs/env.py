# -*- coding: utf-8 -*-
"""'Externally' adjustable config vars."""
import os
from os import environ

# TODO: validation is a good idea.

# Are we in production? False by default.
PRODUCTION = bool(int(environ.get('PRODUCTION', '0')))

# Default HTTPS port by default.
PORT = int(environ['PORT']) if 'PORT' in environ else 443

TRACKING_NUMBER_DEFAULT_VALUE = environ.get('TRACKING_NUMBER_DEFAULT_VALUE', '')

# Everything for tracking through FeDeX.
# Let's minimize possibility of wrong envs.
if PRODUCTION:
	FEDEX_URL = environ['FEDEX_URL']
	FEDEX_TRACKING_API_KEY = environ['FEDEX_TRACKING_API_KEY']
	FEDEX_TRACKING_SECRET_KEY = environ['FEDEX_TRACKING_SECRET_KEY']
else:
	FEDEX_URL = environ['FEDEX_SANDBOX_URL']
	FEDEX_TRACKING_API_KEY = environ['FEDEX_TRACKING_SANDBOX_API_KEY']
	FEDEX_TRACKING_SECRET_KEY = environ['FEDEX_TRACKING_SANDBOX_SECRET_KEY']
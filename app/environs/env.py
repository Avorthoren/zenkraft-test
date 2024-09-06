# -*- coding: utf-8 -*-
"""'Externally' adjustable config vars.
"""
from os import environ

# TODO: validation is a good idea.

# Are we in production? False by default.
PRODUCTION = bool(int(environ.get('PRODUCTION', '0')))

# Default HTTPS port by default.
PORT = int(environ['PORT']) if 'PORT' in environ else 443

TRACKING_NUMBER_DEFAULT_VALUE = environ.get('TRACKING_NUMBER_DEFAULT_VALUE', '')

# Everything for tracking through FedEx.
# Let's minimize possibility of wrong envs by using different input names for
# dev and prod environment.
if PRODUCTION:
	FEDEX_URL = environ['FEDEX_URL']
	FEDEX_TRACKING_API_KEY = environ['FEDEX_TRACKING_API_KEY']
	FEDEX_TRACKING_SECRET_KEY = environ['FEDEX_TRACKING_SECRET_KEY']
else:
	# '_SANDBOX' added for all input names.
	FEDEX_URL = environ['FEDEX_SANDBOX_URL']
	FEDEX_TRACKING_API_KEY = environ['FEDEX_TRACKING_SANDBOX_API_KEY']
	FEDEX_TRACKING_SECRET_KEY = environ['FEDEX_TRACKING_SANDBOX_SECRET_KEY']

# -*- coding: utf-8 -*-
"""Handles FedEx tracking API.
Should be implemented as class if we want to use many carriers.

Mock tracking numbers:
https://www.fedex.com/en-us/developer/web-services/process.html#develop
Apparently, there is no possibility to test non-existent numbers on sandbox...
"""
import asyncio
import json
from typing import Optional, Union, Callable, Awaitable

from tornado import httputil
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError

from .common import CarrierTrackingError
from app.carriers_auth import fedex as fedex_auth
from app.environs import env


_BASE_URL = env.FEDEX_URL
_API_KEY = env.FEDEX_TRACKING_API_KEY
_SECRET_KEY = env.FEDEX_TRACKING_SECRET_KEY
# Will be generated (and regenerated) on demand.
_BEARER_TOKEN = None


class FedexTrackingError(CarrierTrackingError):
	pass


async def _get_bearer_token() -> str:
	return await fedex_auth.get_auth_token(api_key=_API_KEY, secret_key=_SECRET_KEY)


async def _get_bearer_token_v2() -> str:
	return await fedex_auth.get_auth_token_v2(api_key=_API_KEY, secret_key=_SECRET_KEY)

_BearerGetter_T = Callable[[], Awaitable[str]]


async def _make_request(
	endpoint: str,
	method: str = 'POST',
	headers: Optional[Union[dict[str, str], httputil.HTTPHeaders]] = None,
	body: Optional[Union[bytes, str]] = None,
	auth: _BearerGetter_T = _get_bearer_token
):
	"""Makes request to tracking API, returns JSON.

	`endpoint` - URL of needed endpoint relative to _BASE_URL.
	`method` - HTTP method.
	`headers` - additional headers.
	`body` - prepared request body.
	`auth` - authorization method.
	"""
	# Prepare request.
	http_client = AsyncHTTPClient()
	request = HTTPRequest(url=_BASE_URL + endpoint, method=method, body=body, headers=headers)

	# Handle authorization.
	cold_request = False
	global _BEARER_TOKEN
	if _BEARER_TOKEN is None:
		cold_request = True
		_BEARER_TOKEN = await auth()
	request.headers['Authorization'] = f'Bearer {_BEARER_TOKEN}'

	# Make the request.
	try:
		response = await http_client.fetch(request)
	except HTTPError as e:
		# If we get 401, most probably, the token was expired.
		# If we haven't just generated fresh token - try to get a new one.
		if e.code == 401 and not cold_request:
			# Clean token just in case generation fails.
			_BEARER_TOKEN = None
			# Generate fresh token.
			_BEARER_TOKEN = await auth()
			request.headers['Authorization'] = f'Bearer {_BEARER_TOKEN}'
			# Repeat the request with new token.
			response = await http_client.fetch(request)
		else:
			raise

	raw_body = response.body.decode()
	response_data = json.loads(raw_body)

	return response_data


async def _get_tracking_info(
	body: Union[str, bytes],
	endpoint: str = '/track/v1/trackingnumbers',
	auth: _BearerGetter_T = _get_bearer_token
) -> dict:
	"""Common logic of v1 and v2 of tracking API.

	`body` - prepared request body.
	`endpoint` - URL of needed endpoint relative to _BASE_URL.
	`auth` - authorization method.

	FedexTrackingError will be raised in case of tracking or auth errors.
	"""
	try:
		response_data = await _make_request(
			endpoint,
			method='POST',
			headers={'Content-Type': 'application/json'},
			body=body,
			auth=auth
		)
	except (fedex_auth.CarrierAuthError, HTTPError) as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Can\'t get info from FedEx') from e

	# TODO: If we want to use this in logic, we should make proper validation.
	try:
		tracking_info = response_data['output']
	except KeyError as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Invalid response from FedEx') from e

	return tracking_info


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get FedEx tracking info by tracking number."""
	body = json.dumps({
			"trackingInfo": [
				{"trackingNumberInfo": {"trackingNumber": tracking_number}}
			],
			"includeDetailedScans": True
		},
		separators=(',', ':')
	)
	return await _get_tracking_info(body)


async def get_tracking_info_v2(tracking_number: str) -> dict:
	"""Get FedEx tracking info (v2) by tracking number."""
	body = json.dumps({
			"appDeviceType": "WTRK",
			"appType": "WTRK",
			"supportCurrentLocation": True,
			"trackingInfo": [{
				"trackNumberInfo": {
					"trackingCarrier": "",
					"trackingNumber": tracking_number,
					"trackingQualifier": ""
				}
			}],
			"uniqueKey": "",
			"guestAuthenticationToken": ""
		},
		separators=(',', ':')
	)
	return await _get_tracking_info(
		body,
		endpoint='/track/v2/shipments',
		auth=_get_bearer_token_v2
	)


async def main():
	"""For local manual testing."""
	tracking_info = await get_tracking_info(env.TRACKING_NUMBER_DEFAULT_VALUE)
	print(tracking_info)


if __name__ == '__main__':
	asyncio.run(main())

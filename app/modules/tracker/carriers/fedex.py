# -*- coding: utf-8 -*-
"""Handles FeDeX tracking API.
Should be implemented as class if we want to use many carriers.
"""
import asyncio
import json
from typing import Optional, Union

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


async def _make_request(
	endpoint: str,
	method: str = 'POST',
	headers: Optional[Union[dict[str, str], httputil.HTTPHeaders]] = None,
	body: Optional[Union[bytes, str]] = None
):
	"""Makes request to tracking API, returns JSON."""
	http_client = AsyncHTTPClient()
	request = HTTPRequest(url=_BASE_URL + endpoint, method=method, body=body, headers=headers)
	# Handle authorization.
	cold_request = False
	global _BEARER_TOKEN
	if _BEARER_TOKEN is None:
		cold_request = True
		_BEARER_TOKEN = await _get_bearer_token()

	request.headers['Authorization'] = f'Bearer {_BEARER_TOKEN}'
	try:
		response = await http_client.fetch(request)
	except HTTPError as e:
		# If we get 401, most probably, token was expired.
		# If we haven't just generated fresh token - try to get a new one.
		if e.code == 401 and not cold_request:
			# Clean token just in case generation fails.
			_BEARER_TOKEN = None
			# Generate fresh token.
			_BEARER_TOKEN = await _get_bearer_token()
			request.headers['Authorization'] = f'Bearer {_BEARER_TOKEN}'
			response = await http_client.fetch(request)
		else:
			raise

	raw_body = response.body.decode()
	response_data = json.loads(raw_body)

	return response_data


async def get_tracking_info(tracking_number: str) -> dict:
	body = json.dumps({
			"trackingInfo": [
				{"trackingNumberInfo": {"trackingNumber": tracking_number}}
			],
			"includeDetailedScans": True
		},
		separators=(',', ':')
	)

	try:
		response_data = await _make_request(
			endpoint='/track/v1/trackingnumbers',
			method='POST',
			headers={'Content-Type': 'application/json'},
			body=body
		)
	except (fedex_auth.CarrierAuthError, HTTPError) as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Can\'t get info from FeDeX') from e

	# TODO: If we want to use this in logic, we should make proper validation.
	try:
		tracking_info = response_data['output']
	except KeyError as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Invalid response from FeDeX') from e

	return tracking_info


async def main():
	tracking_info = await get_tracking_info(env.TRACKING_NUMBER_DEFAULT_VALUE)
	print(tracking_info)


if __name__ == '__main__':
	asyncio.run(main())

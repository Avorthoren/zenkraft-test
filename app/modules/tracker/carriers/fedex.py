# -*- coding: utf-8 -*-
"""Handles FedEx tracking API.
Should be implemented as class if we want to use many carriers.

Mock tracking numbers:
https://www.fedex.com/en-us/developer/web-services/process.html#develop
Apparently, there is no possibility to test non-existent numbers on REST
sandbox, because their virtualized response always corresponds to existing
number.
Regarding SOAP: there is no reliable way of testing using their API directly,
because response for the same number could be different each time.
Here are some numbers which worked at least once:
61292701078443410536
02394653018047202719
568838414941
797806677146

Just in case...
https://github.com/jzempel/fedex/blob/master/fedex/wsdls/beta/TrackService_v10.wsdl
"""
import asyncio
import json
from typing import Optional, Union, Callable, Awaitable

# httpx is used only because of zeep, and it is in zeep's dependencies.
# If it will be removed from zeep's dependencies, we would need to rewrite code.
# That's why we shouldn't include httpx in requirements.txt explicitly, so
# we will find out changes in zeep's logic right away, and not when we realize
# that our application doesn't catch exceptions properly.
import httpx
from tornado import httputil
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
from zeep import AsyncClient as AsyncSOAPClient
from zeep.helpers import serialize_object as zeep_serialize
from zeep.exceptions import Error as ZeepError

from app.modules.tracker.carriers.common import CarrierTrackingError
from app.carriers_auth import fedex as fedex_auth
from app.environs import env


if env.FEDEX_TRACKING_USE_SOAP:
	# For SOAP FedEx API:
	_SOAP_CLIENT = AsyncSOAPClient('app/modules/tracker/carriers/fedex.wsdl')
	_SOAP_TYPE_FACTORY = _SOAP_CLIENT.type_factory('ns0')
	# .WebAuthenticationDetail
	_SOAP_AUTH = _SOAP_TYPE_FACTORY.WebAuthenticationDetail(
		ParentCredential={
			'Key': env.FEDEX_TRACKING_SOAP_PARENT_KEY,
			'Password': env.FEDEX_TRACKING_SOAP_PARENT_PASSWORD
		},
		UserCredential={
			'Key': env.FEDEX_TRACKING_SOAP_USER_KEY,
			'Password': env.FEDEX_TRACKING_SOAP_USER_PASSWORD
		}
	)
	# .ClientDetail
	_SOAP_CLIENT_DETAIL = _SOAP_TYPE_FACTORY.ClientDetail(
		AccountNumber=env.FEDEX_TRACKING_SOAP_CLIENT_ACCOUNT,
		MeterNumber=env.FEDEX_TRACKING_SOAP_CLIENT_METER
	)
	# .Version
	_SOAP_VERSION = _SOAP_TYPE_FACTORY.VersionId(
		ServiceId='trck',
		Major=env.FEDEX_TRACKING_SOAP_VERSION_MAJOR,
		Intermediate=env.FEDEX_TRACKING_SOAP_VERSION_MIDDLE,
		Minor=env.FEDEX_TRACKING_SOAP_VERSION_MINOR
	)
else:
	# For REST FedEx API:
	_BASE_URL = env.FEDEX_URL
	_API_KEY = env.FEDEX_TRACKING_API_KEY
	_SECRET_KEY = env.FEDEX_TRACKING_SECRET_KEY
	# Will be generated (and regenerated) on demand.
	_BEARER_TOKEN = None


class FedexTrackingError(CarrierTrackingError):
	pass


class FedexTrackingSOAPConnectError(FedexTrackingError):
	pass


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get tracking info by tracking number.

	Uses REST or SOAP depending on env.FEDEX_TRACKING_USE_SOAP.
	REST and SOAP endpoints have different response structures, so this logic
	is used only for the sake of the demonstration.
	"""
	getter = _get_tracking_info_soap if env.FEDEX_TRACKING_USE_SOAP else _get_tracking_info_rest_v1

	return await getter(tracking_number)


async def _get_bearer_token() -> str:
	return await fedex_auth.get_auth_token(api_key=_API_KEY, secret_key=_SECRET_KEY)


async def _get_bearer_token_v2() -> str:
	return await fedex_auth.get_auth_token_v2(api_key=_API_KEY, secret_key=_SECRET_KEY)

_BearerGetter_T = Callable[[], Awaitable[str]]


async def _make_request_rest(
	endpoint: str,
	method: str = 'POST',
	headers: Optional[Union[dict[str, str], httputil.HTTPHeaders]] = None,
	body: Optional[Union[bytes, str]] = None,
	auth: _BearerGetter_T = _get_bearer_token
):
	"""Makes request to REST tracking API, returns serialized JSON.

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


async def _get_tracking_info_rest(
	body: Union[str, bytes],
	endpoint: str = '/track/v1/trackingnumbers',
	auth: _BearerGetter_T = _get_bearer_token
) -> dict:
	"""Common logic of v1 and v2 of REST tracking API.

	`body` - prepared request body.
	`endpoint` - URL of needed endpoint relative to _BASE_URL.
	`auth` - authorization method.

	FedexTrackingError will be raised in case of tracking or auth errors.
	"""
	try:
		response_data = await _make_request_rest(
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


async def _get_tracking_info_rest_v1(tracking_number: str) -> dict:
	"""Get tracking info (v1) by tracking number using REST."""
	body = json.dumps({
			"trackingInfo": [
				{"trackingNumberInfo": {"trackingNumber": tracking_number}}
			],
			"includeDetailedScans": True
		},
		separators=(',', ':')
	)
	return await _get_tracking_info_rest(body)


async def _get_tracking_info_rest_v2(tracking_number: str) -> dict:
	"""Get tracking info (v2) by tracking number using REST.

	NOT TESTED!
	"""
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
	return await _get_tracking_info_rest(
		body,
		endpoint='/track/v2/shipments',
		auth=_get_bearer_token_v2
	)


async def _make_request_soap(operation_name: str, /, *args, **kwargs):
	"""Makes request to REST tracking API, returns JSON.

	`operation_name` - specific operation to call in SOAP service.
	`*args` and `**kwargs` will be passed to the operation.
	"""
	try:
		operation = _SOAP_CLIENT.service.__getattr__(operation_name)
	except AttributeError as e:
		# TODO: logging can be added here
		# Wrong operation name.
		raise FedexTrackingSOAPConnectError('Can\'t get info from FedEx') from e

	try:
		response = await operation(
			*args,
			WebAuthenticationDetail=_SOAP_AUTH,
			ClientDetail=_SOAP_CLIENT_DETAIL,
			Version=_SOAP_VERSION,
			**kwargs
		)
	except httpx.ConnectError as e:
		# TODO: logging can be added here
		# Wrong service address in WSDL file, or service is 'offline', etc.
		# Unfortunately, zeep doesn't reraise such errors using its own
		# exception classes, but uses third party package. Let's hope they will
		# always use it...
		raise FedexTrackingSOAPConnectError('Can\'t get info from FedEx') from e

	if response.HighestSeverity != 'SUCCESS':
		raise FedexTrackingError(response.Notifications[0].Message)

	return response


async def _get_tracking_info_soap(tracking_number: str) -> dict:
	"""Get tracking info by tracking number using SOAP."""
	try:
		response = await _make_request_soap(
			'track',
			SelectionDetails={
				'PackageIdentifier': {
					'Type': 'TRACKING_NUMBER_OR_DOORTAG',
					'Value': tracking_number
				},
			},
			ProcessingOptions=['INCLUDE_DETAILED_SCANS']
		)
	except ZeepError as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Can\'t get info from FedEx') from e

	# Return part of the response that corresponds specifically for tracking
	# info of the requested tracking number.
	try:
		track_details = response['CompletedTrackDetails'][0]['TrackDetails']
	except (KeyError, IndexError) as e:
		# TODO: logging can be added here
		raise FedexTrackingError('Invalid response from FedEx') from e

	tracking_info = {'TrackDetails': zeep_serialize(track_details, dict)}

	return tracking_info


async def main():
	"""For local manual testing."""
	# tracking_info = await get_tracking_info(env.TRACKING_NUMBER_DEFAULT_VALUE)
	# print(tracking_info)

	tracking_info = await _get_tracking_info_soap('02394653018047202719')
	print(tracking_info)


if __name__ == '__main__':
	asyncio.run(main())

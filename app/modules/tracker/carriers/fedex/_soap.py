# -*- coding: utf-8 -*-
"""Handles FedEx SOAP tracking API.
Should be implemented as class if we want to use many carriers.

WARNING!
This module uses many environment variables which will be defined only if
FEDEX_TRACKING_USE_SOAP is True, therefore, make sure it's the case before
importing it.

Mock tracking numbers:
https://www.fedex.com/en-us/developer/web-services/process.html#develop
There is no reliable way of testing using their API directly,
because response for the same number could be different each time.
Here are some numbers which worked at least once:
122816215025810
61292701078443410536
02394653018047202719
568838414941
797806677146

Just in case...
https://github.com/jzempel/fedex/blob/master/fedex/wsdls/beta/TrackService_v10.wsdl
"""
import asyncio
from typing import Awaitable, Protocol

# httpx is used only because of zeep, and it is in zeep's dependencies.
# If it will be removed from zeep's dependencies, we would need to rewrite code.
# That's why we shouldn't include httpx in requirements.txt explicitly, so
# we will find out changes in zeep's logic right away, and not when we realize
# that our application doesn't catch exceptions properly.
import httpx
from zeep import AsyncClient as AsyncSOAPClient
from zeep.helpers import serialize_object as zeep_serialize
from zeep.exceptions import Error as ZeepError
from zeep.proxy import OperationProxy as ZeepOperationProxy

from app.modules.tracker.carriers.fedex.error import FedexTrackingError
from app.environs import env


_SOAP_CLIENT = AsyncSOAPClient('app/modules/tracker/carriers/fedex/fedex.wsdl')
_SOAP_TYPE_FACTORY = _SOAP_CLIENT.type_factory('ns0')


class _AsyncRequestWithCredentials(Protocol):
	def __call__(self, operation: ZeepOperationProxy, /, *args, **kwargs) -> Awaitable:
		pass


# We don't want to build common objects (like credentials) for every
# request we make.
# Credentials are complex mutable objects.
# Unfortunately, underlying zeep method that build zeep-native objects
# from other objects don't accept arbitrary mappings, checking specifically
# for builtin dict. To protect credentials from mutations (and ourselves
# from potential errors) let's isolate them inside this 'factory'.
def _make_request_with_credentials_factory() -> _AsyncRequestWithCredentials:
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

	async def wrapped(
		operation: ZeepOperationProxy,
		/,
		*args,
		**kwargs
	):
		"""Makes request to SOAP tracking API, returns serialized JSON.

		Injects common credentials into request.
		`operation` - specific operation to call in SOAP service.
		`*args` and `**kwargs` will be passed to the operation.
		"""
		return await operation(
			*args,
			WebAuthenticationDetail=_SOAP_AUTH,
			ClientDetail=_SOAP_CLIENT_DETAIL,
			Version=_SOAP_VERSION,
			**kwargs
		)

	return wrapped


# This is low-level function that should be used for SOAP requests.
# Implements _AsyncRequestWithCredentials.
_make_request_with_credentials = _make_request_with_credentials_factory()


class FedexTrackingSOAPConnectError(FedexTrackingError):
	pass


async def _make_request(operation_name: str, /, *args, **kwargs):
	"""Makes request to SOAP tracking API, returns serialized JSON.

	`operation_name` - specific operation to call in SOAP service.
	`args` and `kwargs` will be passed to the operation.
	"""
	try:
		operation = _SOAP_CLIENT.service.__getattr__(operation_name)
	except AttributeError as e:
		# TODO: logging can be added here
		# Wrong operation name.
		raise FedexTrackingSOAPConnectError('Can\'t get info from FedEx') from e

	try:
		response = await _make_request_with_credentials(
			operation,
			*args,
			**kwargs
		)
	except httpx.ConnectError as e:
		# TODO: logging can be added here
		# Wrong service address in WSDL file, or service is 'offline', etc.
		# Unfortunately, zeep doesn't reraise such errors using its own
		# exception classes, that's why we catch third party package exceptions.
		# Let's hope zeep will always use it...
		raise FedexTrackingSOAPConnectError('Can\'t get info from FedEx') from e

	if response.HighestSeverity != 'SUCCESS':
		raise FedexTrackingError(response.Notifications[0].Message)

	return response


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get tracking info by tracking number using SOAP."""
	try:
		response = await _make_request(
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
	tracking_info = await get_tracking_info('02394653018047202719')
	print(tracking_info)


if __name__ == '__main__':
	asyncio.run(main())

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
122816215025810
61292701078443410536
02394653018047202719
568838414941
797806677146

Just in case...
https://github.com/jzempel/fedex/blob/master/fedex/wsdls/beta/TrackService_v10.wsdl
"""
import asyncio

from app.environs import env
# Define API to use.
if env.FEDEX_TRACKING_USE_SOAP:
	import app.modules.tracker.carriers.fedex._soap as _fedex_api
else:
	import app.modules.tracker.carriers.fedex._rest as _fedex_api


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get tracking info by tracking number.

	Uses REST or SOAP depending on env.FEDEX_TRACKING_USE_SOAP.
	REST and SOAP endpoints have different response structures, so this logic
	is used only for the sake of the demonstration.
	"""
	return await _fedex_api.get_tracking_info(tracking_number)


async def main():
	"""For local manual testing."""
	tracking_info = await get_tracking_info(env.TRACKING_NUMBER_DEFAULT_VALUE)
	print(tracking_info)


if __name__ == '__main__':
	asyncio.run(main())

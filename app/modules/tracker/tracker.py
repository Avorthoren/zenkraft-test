# -*- coding: utf-8 -*-
"""Low-level module for tracking info.
"""
import asyncio

from app.modules.tracker.carriers import fedex

# Let's define it here while we have only one carrier.
# It looks like it should be no more than 34, but just in case...
# For input validation:
TRACKING_NUMBER_MAX_LENGTH = 128
# For input UI:
TRACKING_NUMBER_INPUT_SIZE = 35


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get tracking info by tracking number. Currently: from FedEx."""
	tracking_info = await fedex.get_tracking_info(tracking_number)

	return tracking_info


async def main():
	"""For local manual testing."""
	...


if __name__ == '__main__':
	asyncio.run(main())

# -*- coding: utf-8 -*-
"""Low-level module for tracking info.
"""
from .carriers import fedex

# Let's define it here while we have only one carrier.
# It looks like it should be no more than 34, but just in case...
TRACKING_NUMBER_MAX_LENGTH = 128


async def get_tracking_info(tracking_number: str) -> dict:
	"""Get tracking info by tracking number. Currently: from FedEx."""
	tracking_info = await fedex.get_tracking_info(tracking_number)
	return tracking_info


# async def _get_from_fedex_xml(tracking_number: str) -> str:
# 	http_client = AsyncHTTPClient()
# 	request = HTTPRequest(url=config.CARRIER, method='POST', body=_REQUEST, headers={
# 		'Accept': 'image/gif, image/jpeg, image/pjpeg, text/plain, text/html, */*',
# 		'Content-Type': 'text/xml'
# 	})
# 	try:
# 		response = await http_client.fetch(request, raise_error=False)
# 	except Exception as e:
# 		print(e)
# 		return {'Exception': str(e)}
# 	tracking_info = response.body.decode()
#
# 	return tracking_info


def main():
	"""For local manual testing."""
	...


if __name__ == '__main__':
	main()

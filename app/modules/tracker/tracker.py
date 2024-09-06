# -*- coding: utf-8 -*-
"""Low-level module for tracing info.
"""
from .carriers import fedex


async def get_tracking_info(tracking_number: str) -> dict:
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
	...


if __name__ == '__main__':
	main()

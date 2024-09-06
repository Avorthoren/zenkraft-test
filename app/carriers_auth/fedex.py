# -*- coding: utf-8 -*-
"""Handles FeDeX authorization.
Should be implemented as class if we want to use many carriers.
"""
import asyncio
import json
from typing import TypedDict
import urllib.parse

from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError
import voluptuous as vlps
from voluptuous import REMOVE_EXTRA

from .common import CarrierAuthError
from app.environs import env


_BASE_URL = env.FEDEX_URL


class FedexAuthError(CarrierAuthError):
	pass


# Let's make it explicit: describe only keys we are using.
_AUTH_DATA_SCHEMA = vlps.Schema({
	vlps.Required('access_token'): str
}, extra=REMOVE_EXTRA)


class AuthData(TypedDict):
	access_token: str


async def get_auth_data(api_key: str, secret_key: str) -> AuthData:
	http_client = AsyncHTTPClient()
	params = {
		'grant_type': 'client_credentials',
		'client_id': api_key,
		'client_secret': secret_key
	}
	request = HTTPRequest(
		url=_BASE_URL + '/oauth/token',
		method='POST',
		headers={'Content-Type': 'application/x-www-form-urlencoded'},
		body=urllib.parse.urlencode(params)
	)

	try:
		response = await http_client.fetch(request)
	except HTTPError as e:
		# TODO: logging can be added here
		raise FedexAuthError(str(e))

	raw_body = response.body.decode()
	auth_data = json.loads(raw_body)
	try:
		auth_data = _AUTH_DATA_SCHEMA(auth_data)
	except vlps.Error as e:
		# TODO: logging can be added here
		raise FedexAuthError(str(e))

	return auth_data


async def get_auth_token(api_key: str, secret_key: str) -> str:
	auth_data = await get_auth_data(api_key, secret_key)
	return auth_data['access_token']


async def main():
	print(await get_auth_token(
		api_key=env.FEDEX_TRACKING_API_KEY,
		secret_key=env.FEDEX_TRACKING_SECRET_KEY
	))


if __name__ == '__main__':
	asyncio.run(main())

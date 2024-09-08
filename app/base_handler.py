# -*- coding: utf-8 -*-
"""Common module for all handlers in app.api, providing a BaseHandler class that
all handlers should inherit from as well as ApplicationError class.
"""
from contextlib import suppress
import dataclasses
import datetime
from decimal import Decimal
import enum
import json

from tornado import escape
import tornado.web
import voluptuous as vlps


__all__ = ('ApplicationError', 'BaseHandler')


class ApplicationError(tornado.web.HTTPError):
	"""An override of a standard tornado HTTPError class for custom handling."""

	def __init__(self, status_code: int, message: str, *args, **kwargs):
		self.message = message
		super().__init__(status_code, *args, reason=message, **kwargs)


class WideJSONEncoder(json.JSONEncoder):
	"""Custom json encoder: allows to handle:
	 - dataclasses
	 - date/datetime
	 - enums
	 - Decimal
	"""
	def default(self, obj):
		if dataclasses.is_dataclass(obj):
			# If somehow `obj` is not an instance, but dataclass itself,
			# asdict(obj) will raise TypeError
			with suppress(TypeError):
				return dataclasses.asdict(obj)

		# One could just try last line except TypeError: return str(obj),
		# but let's keep it explicit way and add new types when we need it:
		if isinstance(obj, (
			datetime.date,
			enum.Enum,
			Decimal
		)):
			return str(obj)

		return super().default(obj)


# pylint: disable=abstract-method
class BaseHandler(tornado.web.RequestHandler):
	"""Base API class for all endpoints.

	Inherit from this if you want to create a new handler.
	"""
	def set_default_headers(self):
		self.set_header('Access-Control-Allow-Origin', '*')
		self.set_header('Access-Control-Allow-Credentials', 'true')
		self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
		self.set_header(
			'Access-Control-Allow-Headers',
			'Content-Type, Accept-Version, Authorization, CrossDomain, WithCredentials'
		)

	def options(self, *args, **kwargs):  # pylint: disable=arguments-differ
		"""All OPTIONS requests are ignored with silent OK by default."""
		self.finish()

	def write(self, chunk):
		"""Overload of Tornado RequestHandler.write().

		Implemented for default conversion to string while json.dumps().
		This allows to direct usage of Date (and other) objects in response.
		"""
		if isinstance(chunk, dict):
			chunk = json.dumps(
				chunk,
				cls=WideJSONEncoder,
				separators=(',', ':')
			).replace("</", "<\\/")

			self.set_header("Content-Type", "application/json; charset=UTF-8")

		super().write(chunk)

	def write_error(self, statusCode, **kwargs):  # pylint: disable=arguments-differ
		"""Send error response to client based on HTTPError-derived exception.

		NOTE:
		This should not be called directly.

		Allows to easily report errors via ApplicationError, specifying desired
		code and message. Tornado catches all HTTPError-derived exceptions and
		feeds to this class.

		By default, though, it is unwieldy (impossible to use custom message for
		a standard error), hence custom implementation.
		"""
		try:
			message = kwargs["exc_info"][0].message
		except (KeyError, IndexError, AttributeError):
			message = self._reason

		self.set_status(statusCode)
		self.finish({'message': message})

	def parse_json(self, json_: str = None):
		"""Parses data from json: either given string or self.request.body."""
		if not json_:
			json_ = self.request.body

		try:
			request = escape.json_decode(json_)
		except escape.json.JSONDecodeError as e:
			raise ApplicationError(status_code=400, message="Bad JSON in request body") from e

		return request

	def validate(
		self,
		schema: vlps.Schema,
		data=None,
		http_error_code: int = 400,
		custom_message: str = None
	):
		"""Validates `data` according to Voluptuous `schema`.

		If `data` is None then request body will be used.
		`data` will be checked for compliance with the `schema`. New constructed
		object will be returned. `schema` may contain transform instructions, so
		the returned object may be different from the original `data`.

		In case of validation error ApplicationError with given error_code
		will be raised with given message or validator message by default.
		"""
		if not isinstance(http_error_code, int):
			raise TypeError("onErrorStatusCode should be integer")

		# Validate HTTP error code
		if http_error_code < 400 or http_error_code >= 600:
			raise ValueError("http_error_code should be in range [400, 600)")

		if data is None:
			data = self.parse_json()

		try:
			data = schema(data)
		except vlps.Error as e:
			message = str(e) if custom_message is None else custom_message
			raise ApplicationError(
				status_code=http_error_code,
				message=message
			) from e

		# Validated data
		return data

	def validate_query_string(self, schema: vlps.Schema):
		"""Validate GET request args with Voluptuous.

		All query-string args zipped into dict which then validated by specified
		voluptuous schema.
		Don't forget to use Coerces in your schema, because all GET-request
		args are strings.
		"""
		return self.validate(
			schema,
			{k: self.get_argument(k) for k in self.request.arguments}
		)

	def validate_body(self, schema: vlps.Schema):
		"""Validate request body args with Voluptuous.

		Should be used for form-data, x-www-form-urlencoded, etc.
		All body args zipped into dict which then validated by specified
		voluptuous schema.
		Don't forget to use Coerces in your schema, because all body args
		are strings.
		"""
		return self.validate(
			schema,
			{k: self.get_body_argument(k) for k in self.request.body_arguments}
		)

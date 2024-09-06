# -*- coding: utf-8 -*-
"""Module with handler that allows to GET tracking info.
"""
from app.base_handler import BaseHandler
from app.environs import env
from app.modules.tracker import tracker
from app.validation.tracker import USER_REQUEST_SCHEMA


class TrackerUIHandler(BaseHandler):
	def get(self):
		self.render(
			'tracker.html',
			default_value=env.TRACKING_NUMBER_DEFAULT_VALUE
		)


class TrackerHandler(BaseHandler):
	async def get(self):
		"""Get tracking info by tracking number"""
		request = self.validate_query_string(USER_REQUEST_SCHEMA)

		result = await tracker.get_tracking_info(**request)

		self.write(result)

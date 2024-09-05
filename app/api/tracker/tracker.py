# -*- coding: utf-8 -*-
"""Module with handler that allows to GET tracking info.
"""
from app.base_handler import BaseHandler
from app.modules.tracker import tracker
from app.validation.tracker import USER_REQUEST_SCHEMA


class TrackerHandler(BaseHandler):
	async def get(self):
		"""Get tracking info by tracking number"""
		request = self.validate(USER_REQUEST_SCHEMA)

		result = tracker.get_tracking_info(**request)

		self.write(result)

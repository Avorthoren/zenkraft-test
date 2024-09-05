# -*- coding: utf-8 -*-
"""Module with handler that allows to GET tracking info.
"""
from app.base_handler import BaseHandler, ApplicationError
from app.modules.tracker import tracker
from app.validation.tracker import USER_REQUEST_SCHEMA


class TrackerUIHandler(BaseHandler):
	def get(self):
		self.render('tracker.html')


class TrackerHandler(BaseHandler):
	async def get(self):
		"""Get tracking info by tracking number"""
		request = self.validate_query_string(USER_REQUEST_SCHEMA)

		raise ApplicationError(status_code=503, message='No response from FeDex')

		result = tracker.get_tracking_info(**request)

		self.write(result)

# -*- coding: utf-8 -*-
"""Module with handler that allows to GET tracking info.
"""
from app.base_handler import BaseHandler, ApplicationError
from app.environs import env
# from app.modules.tracker import tracker
from app.modules.tracker.carriers.common import CarrierTrackingError
import app.modules.tracker.tracker as tracker

from app.validation.tracker import USER_REQUEST_SCHEMA


class TrackerUIHandler(BaseHandler):
	def get(self):
		self.render(
			'tracker.html',
			tacking_number_default_value=env.TRACKING_NUMBER_DEFAULT_VALUE,
			tracking_number_input_size=tracker.TRACKING_NUMBER_INPUT_SIZE,
			tacking_number_max_length=tracker.TRACKING_NUMBER_MAX_LENGTH
		)


class TrackerHandler(BaseHandler):
	async def get(self):
		"""Get tracking info by tracking number. Currently: from FedEx."""
		request = self.validate_query_string(USER_REQUEST_SCHEMA)

		try:
			result = await tracker.get_tracking_info(**request)
		except CarrierTrackingError as e:
			# Blame it on carrier.
			raise ApplicationError(status_code=502, message=str(e))

		self.write(result)

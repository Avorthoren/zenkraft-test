# -*- coding: utf-8 -*-
"""Module with handler that allows to GET current running application version.
"""
from app.base_handler import BaseHandler


class VersionHandler(BaseHandler):
	def get(self):
		"""Return current application version."""
		self.write({"version": self.application.version})

# -*- coding: utf-8 -*-
"""Module with health check handler required by Amazon, responds with "ok"
to any GET/POST request
"""
import tornado.web


class HealthCheckHandler(tornado.web.RequestHandler):
	"""Can be used to health-check requests"""
	def get(self):
		self.set_status(200)
		self.write("ok")

	def post(self):
		self.set_status(201)
		self.write("ok")

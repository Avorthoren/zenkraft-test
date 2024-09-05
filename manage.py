#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main module of the program, executable."""
import asyncio
import os.path

from tornado.options import define, options
import tornado.web

from app import api
from app.environs import env


define("port", default=env.PORT, help="run on the given port", type=int)

# pylint: disable=bad-whitespace
handlers = [
	(r"/api/healthcheck",                           api.healthcheck.HealthCheckHandler),
	(r"/api/version",                               api.version.VersionHandler),
	(r"/api/static/(.*)",                           tornado.web.StaticFileHandler, {"path": "app/static"}),

	# Front-end
	(r"/",                                          api.tracker.TrackerUIHandler),

	# API
	(r"/api/tracker",                               api.tracker.TrackerHandler),
]
# pylint: enable=bad-whitespace


class Application(tornado.web.Application):
	"""Main application class."""
	def __init__(self):
		# Read app version.
		workdir = os.path.dirname(os.path.realpath('__file__'))
		with open(os.path.join(workdir, 'VERSION')) as file:
			self.version = file.read().strip()

		super(Application, self).__init__(handlers)


async def main():
	"""Main function of the program."""
	# # Create new asyncio loop for server
	# loop = asyncio.get_event_loop()
	#
	# tornado.options.parse_command_line()
	# http_server = Application(loop)
	# http_server.listen(options.port)
	# # Rewrite config if port directly defined through command line.
	# env.PORT = options.port
	#
	# # The asyncio loop created at the beginning is started now. Coroutines (and
	# # server in general) are running from this point onwards.
	# loop.run_forever()
	server = Application()
	server.listen(options.port)
	await asyncio.Event().wait()


if __name__ == "__main__":
	asyncio.run(main())

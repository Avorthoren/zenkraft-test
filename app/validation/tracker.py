# -*- coding: utf-8 -*-
"""Module with validations schemas for client tracker requests.
"""
import voluptuous as vlps

from app.modules.tracker.tracker import TRACKING_NUMBER_MAX_LENGTH

# Used to validate TrackerHandler.get request.
USER_REQUEST_SCHEMA = vlps.Schema({
	'tracking_number': vlps.All(
		str,
		vlps.Length(min=1, max=TRACKING_NUMBER_MAX_LENGTH)
	)
})

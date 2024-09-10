# -*- coding: utf-8 -*-
"""Separate file for base exception class(es) to avoid circular import.
"""
from app.modules.tracker.carriers.common import CarrierTrackingError


class FedexTrackingError(CarrierTrackingError):
	"""Base class for all FedEx tracking errors."""
	pass

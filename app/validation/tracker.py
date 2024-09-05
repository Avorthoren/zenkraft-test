# -*- coding: utf-8 -*-
"""Module with validations schemas for tracker requests.
"""
import voluptuous as vlps


USER_REQUEST_SCHEMA = vlps.Schema({'tracking_number': str})

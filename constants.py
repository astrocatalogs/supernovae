"""Supernovae specific constant variables.
"""
from astropy import constants as const
from astropy import units as un


CLIGHT = const.c.cgs.value
KM = (1.0 * un.km).cgs.value

MAX_VISUAL_BANDS = [
    ['B', 'b', 'g'],  # B-like bands first
    ['V', 'G'],       # if not, V-like bands
    ['R', 'r']        # if not, R-like bands
]

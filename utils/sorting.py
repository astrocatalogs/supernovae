"""
"""
from ..constants import PREF_KINDS

__all__ = ['frame_priority']


def frame_priority(attr):
    if 'kind' in attr:
        if attr['kind'] in PREF_KINDS:
            return PREF_KINDS.index(attr['kind'])
        else:
            return len(PREF_KINDS)
    return len(PREF_KINDS)

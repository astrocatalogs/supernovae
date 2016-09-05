"""
"""
from astrocats.catalog.quantity import QUANTITY

__all__ = ['frame_priority']


def frame_priority(quantity, key):
    if quantity.get(QUANTITY.KIND, ''):
        if quantity[QUANTITY.KIND] in key.kind_preference:
            return key.kind_preference.index(quantity[QUANTITY.KIND])
        else:
            return len(key.kind_preference)
    return len(key.kind_preference)

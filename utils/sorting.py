"""
"""
from astrocats.catalog.quantity import QUANTITY

__all__ = ['frame_priority']


def frame_priority(quantity):
    if quantity.get(QUANTITY.KIND, ''):
        if quantity[QUANTITY.KIND] in quantity.kind_preference:
            return quantity.kind_preference.index(quantity[QUANTITY.KIND])
        else:
            return len(quantity.kind_preference)
    return len(quantity.kind_preference)

'''Utility functions related to comparing quanta to one another to determine if
they are unique.
'''
from decimal import Decimal

__all__ = ['same_tag_num', 'same_tag_str']


def same_tag_num(photo, val, tag, canbelist=False):
    '''
    issame = (
        (tag not in photo and not val) or
        (tag in photo and not val) or
        (tag in photo and
         ((not canbelist and Decimal(photo[tag]) == Decimal(val)) or
          (canbelist and
           ((isinstance(photo[tag], str) and isinstance(val, str) and
             Decimal(photo[tag]) == Decimal(val)) or
            (isinstance(photo[tag], list) and isinstance(val, list) and
             photo[tag] == val))))))
    '''

    '''
    if tag not in photo and not val:
        return True

    if tag in photo and not val:
        return True
    '''

    if not val:
        return True

    if tag in photo:
        if not canbelist and Decimal(photo[tag]) == Decimal(val):
            return True

        if canbelist:
            if ((isinstance(photo[tag], str) and
                 isinstance(val, str) and
                 Decimal(photo[tag]) == Decimal(val))):
                return True

            if ((isinstance(photo[tag], list) and
                 isinstance(val, list) and
                 photo[tag] == val)):
                return True

    return False


def same_tag_str(photo, val, tag):
    issame = ((tag not in photo and not val) or (
        tag in photo and not val) or (tag in photo and photo[tag] == val))
    return issame

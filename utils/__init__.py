"""
"""

from decimal import Decimal, localcontext

from . import clean, compare, sorting
from .clean import *
from .compare import *
from .sorting import *

__all__ = []
__all__.extend(sorting.__all__)
__all__.extend(clean.__all__)
__all__.extend(compare.__all__)

from astrocats.utils.digits import get_sig_digits
from astrocats.structures.struct import PHOTOMETRY


DEFAULT_UL_SIGMA = 5.0
DEFAULT_ZP = 30.0
D25 = Decimal('2.5')


def set_pd_mag_from_counts(photodict, c='', ec='', lec='', uec='',
                           zp=DEFAULT_ZP, sig=DEFAULT_UL_SIGMA):
    """Set photometry dictionary from a counts measurement."""
    with localcontext() as ctx:
        if lec == '' or uec == '':
            lec = ec
            uec = ec
        prec = max(
            get_sig_digits(str(c), strip_zeroes=False),
            get_sig_digits(str(lec), strip_zeroes=False),
            get_sig_digits(str(uec), strip_zeroes=False)) + 1
        ctx.prec = prec
        dlec = Decimal(str(lec))
        duec = Decimal(str(uec))
        if c != '':
            dc = Decimal(str(c))
        dzp = Decimal(str(zp))
        dsig = Decimal(str(sig))
        photodict[PHOTOMETRY.ZERO_POINT] = str(zp)
        if c == '' or float(c) < float(sig) * float(uec):
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
            photodict[PHOTOMETRY.UPPER_LIMIT_SIGMA] = str(sig)
            photodict[PHOTOMETRY.MAGNITUDE] = str(dzp - (D25 * (dsig * duec
                                                                ).log10()))
            dnec = Decimal('10.0') ** (
                (dzp - Decimal(photodict[PHOTOMETRY.MAGNITUDE])) / D25)
            photodict[PHOTOMETRY.E_UPPER_MAGNITUDE] = str(D25 * (
                (dnec + duec).log10() - dnec.log10()))
        else:
            photodict[PHOTOMETRY.MAGNITUDE] = str(dzp - D25 * dc.log10())
            photodict[PHOTOMETRY.E_UPPER_MAGNITUDE] = str(D25 * (
                (dc + duec).log10() - dc.log10()))
            photodict[PHOTOMETRY.E_LOWER_MAGNITUDE] = str(D25 * (
                dc.log10() - (dc - dlec).log10()))

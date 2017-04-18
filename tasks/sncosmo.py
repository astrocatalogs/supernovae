"""Import tasks for the Sloan Digital Sky Survey.
"""
import numpy as np
import sncosmo
from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.utils import pbar
from astropy.table import Table

from ..supernova import SUPERNOVA


def do_sncosmo(catalog):
    import warnings
    warnings.filterwarnings("ignore", message="fcn returns Nan")
    warnings.filterwarnings("ignore", message="overflow encountered in power")
    warnings.filterwarnings(
        "ignore", message="Dropping following bands from data:*")
    warnings.filterwarnings("ignore", message="overflow encountered in square")
    warnings.filterwarnings(
        "ignore", message="invalid value encountered in multiply")
    warnings.filterwarnings(
        "ignore", message="overflow encountered in multiply")

    task_str = catalog.get_current_task_str()

    for event in pbar(catalog.entries, task_str):
        catalog.add_entry(event, delete=False)
        if (SUPERNOVA.PHOTOMETRY not in catalog.entries[event]  # or
                # SUPERNOVA.REDSHIFT in catalog.entries[event] or
                # SUPERNOVA.LUM_DIST in catalog.entries[event]
            ):
            catalog.entries[event] = catalog.entries[event].get_stub()
            continue
        photodat = []
        for photo in catalog.entries[event][SUPERNOVA.PHOTOMETRY]:
            if (photo.get(PHOTOMETRY.BAND_SET, '') == 'SDSS' and
                    PHOTOMETRY.TIME in photo and PHOTOMETRY.BAND in photo and
                    PHOTOMETRY.FLUX_DENSITY in photo and
                    PHOTOMETRY.E_FLUX_DENSITY in photo and
                    PHOTOMETRY.UPPER_LIMIT not in photo):
                photodat.append(
                    (float(photo[PHOTOMETRY.TIME]),
                     'sdss' + photo[PHOTOMETRY.BAND].replace("'", ''),
                     float(photo[PHOTOMETRY.FLUX_DENSITY]),
                     float(photo[PHOTOMETRY.E_FLUX_DENSITY]),
                     float(photo[PHOTOMETRY.ZERO_POINT]), 'ab'))
            elif (photo.get(PHOTOMETRY.BAND_SET, '') == 'MegaCam' and
                  PHOTOMETRY.TIME in photo and PHOTOMETRY.BAND in photo and
                  PHOTOMETRY.COUNT_RATE in photo and
                  PHOTOMETRY.E_COUNT_RATE in photo and
                  PHOTOMETRY.UPPER_LIMIT not in photo):
                photodat.append(
                    (float(photo[PHOTOMETRY.TIME]),
                     'sdss' + photo[PHOTOMETRY.BAND].replace("'", ''),
                     float(photo[PHOTOMETRY.COUNT_RATE]),
                     float(photo[PHOTOMETRY.E_COUNT_RATE]),
                     float(photo[PHOTOMETRY.ZERO_POINT]), 'bd17'))
        if len(photodat) < 20:
            catalog.entries[event] = catalog.entries[event].get_stub()
            continue
        table = Table(
            rows=photodat,
            names=('time', 'band', 'flux', 'fluxerr', 'zp', 'zpsys'))
        if (catalog.entries[event].get(SUPERNOVA.CLAIMED_TYPE, [{
                QUANTITY.VALUE: ''
        }])[0][QUANTITY.VALUE] == 'Ia'):
            source = sncosmo.get_source('salt2', version='2.4')
            model = sncosmo.Model(source=source)
            mredchisq = np.inf
            fm = None
            for zmin in np.linspace(0.0, 1.0, 19):
                zmax = zmin + 0.1  # Overlapping intervals
                try:
                    resl, fml = sncosmo.fit_lc(
                        table,
                        model, ['z', 't0', 'x0', 'x1', 'c'],
                        bounds={'z': (zmin, zmax)})
                except RuntimeError:
                    continue
                except sncosmo.fitting.DataQualityError:
                    break
                if resl.ndof < 15:
                    continue
                redchiq = resl.chisq / resl.ndof
                if (redchiq < mredchisq and redchiq < 2.0 and not np.isclose(
                        zmin, fml.get('z'), rtol=1.0e-3) and not np.isclose(
                            zmax, fml.get('z'), rtol=1.e-3)):
                    mredchisq = resl.chisq
                    res, fm = resl, fml

            if fm:
                print(event, res.chisq / res.ndof,
                      fm.get('z'),
                      catalog.entries[event][SUPERNOVA.REDSHIFT][0]['value']
                      if SUPERNOVA.REDSHIFT in catalog.entries[event] else
                      'no redshift')
                # source = catalog.entries[event].add_source(
                #     bibcode='2014A&A...568A..22B')
                # catalog.entries[event].add_quantity(SUPERNOVA.REDSHIFT,
                #                                     str(fm.get('z')), source)
                catalog.journal_entries()
            else:
                catalog.entries[event] = catalog.entries[event].get_stub()

    return

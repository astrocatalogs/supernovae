"""Import tasks for PTSS."""
import os
import json
from glob import glob
from astropy import units as un

from astrocats.catalog.utils import jd_to_mjd, pbar, pretty_num, uniq_cdl
from astropy.time import Time as astrotime
from astropy.coordinates import SkyCoord as coord

from decimal import Decimal
from datetime import datetime

from ..supernova import SUPERNOVA
from astrocats.catalog.photometry import PHOTOMETRY


def do_ptss_meta(catalog):
    task_str = catalog.get_current_task_str()

    years = list(range(2015, datetime.today().year + 1))
    for year in years:
        jsontxt = None
        while jsontxt is None:
            try:
                jsontxt = catalog.load_url(
                    'http://www.cneost.org/ptss/fetchlist.php?vip=sn&gdate=' + str(year),
                    os.path.join(catalog.get_current_task_repo(), 'PTSS/catalog-' + str(year) + '.json'),
                    json_sort='name', timeout=5)
            except Exception:
                pass

        meta = json.loads(jsontxt)
        for met in pbar(meta, task_str + ' - ' + str(year)):
            oldname = met['name']
            name = catalog.add_entry(oldname)
            source = catalog.entries[name].add_source(
                name='PMO & Tsinghua Supernova Survey (PTSS)',
                url='http://www.cneost.org/ptss/index.php')
            coo = coord(met['ra'], met['dec'], unit=(un.deg, un.deg))
            catalog.entries[name].add_quantity(SUPERNOVA.RA,
                coo.ra.to_string(unit=un.hour, sep=':'), source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC,
                coo.dec.to_string(unit=un.degree, sep=':'), source)

            if met['filter'] is not None:
                mjd = str(astrotime(met['obsdate'], format='isot').mjd)
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.MAGNITUDE: str(met['mag']),
                    PHOTOMETRY.E_MAGNITUDE: str(met['magerr']),
                    PHOTOMETRY.BAND: met['filter'].replace('sdss-', ''),
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)

        catalog.journal_entries()
    return

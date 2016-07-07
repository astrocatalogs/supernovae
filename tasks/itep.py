"""Import tasks for the Sternberg Astronomical Institute's Supernova Light
Curve Catalog, from the ITEP-SAI group.
"""
import csv
import os
import re
from collections import OrderedDict
from html import unescape

from astrocats.catalog.utils import jd_to_mjd, pbar
from cdecimal import Decimal


def do_itep(catalog):
    task_str = catalog.get_current_task_str()
    itepbadsources = ['2004ApJ...602..571B']
    needsbib = []
    with open(os.path.join(catalog.get_current_task_repo(),
                           'itep-refs.txt'), 'r') as refs_file:
        refrep = refs_file.read().splitlines()
    refrepf = dict(list(zip(refrep[1::2], refrep[::2])))
    fname = os.path.join(catalog.get_current_task_repo(),
                         'itep-lc-cat-28dec2015.txt')
    tsvin = list(csv.reader(open(fname, 'r'),
                            delimiter='|', skipinitialspace=True))
    curname = ''
    for rr, row in enumerate(pbar(tsvin, task_str)):
        if rr <= 1 or len(row) < 7:
            continue
        oldname = 'SN' + row[0].strip()
        mjd = str(jd_to_mjd(Decimal(row[1].strip())))
        band = row[2].strip()
        magnitude = row[3].strip()
        e_magnitude = row[4].strip()
        reference = row[6].strip().strip(',')

        if curname != oldname:
            curname = oldname
            name = catalog.add_entry(oldname)

            sec_reference = ('Sternberg Astronomical Institute '
                             'Supernova Light Curve Catalogue')
            sec_refurl = 'http://dau.itep.ru/sn/node/72'
            sec_source = catalog.entries[name].add_source(
                name=sec_reference, url=sec_refurl, secondary=True)
            catalog.entries[name].add_quantity('alias', oldname, sec_source)

            year = re.findall(r'\d+', name)[0]
            catalog.entries[name].add_quantity(
                'discoverdate', year, sec_source)
        if reference in refrepf:
            bibcode = unescape(refrepf[reference])
            source = catalog.entries[name].add_source(bibcode=bibcode)
        else:
            needsbib.append(reference)
            source = catalog.entries[name].add_source(
                name=reference) if reference else ''

        if bibcode not in itepbadsources:
            catalog.entries[name].add_photometry(time=mjd, band=band,
                                                 magnitude=magnitude,
                                                 e_magnitude=e_magnitude,
                                                 source=sec_source + ',' +
                                                 source)

    # Write out references that could use aa bibcode
    needsbib = list(OrderedDict.fromkeys(needsbib))
    with open('../itep-needsbib.txt', 'w') as bib_file:
        bib_file.writelines(['%ss\n' % ii for ii in needsbib])
    catalog.journal_entries()
    return

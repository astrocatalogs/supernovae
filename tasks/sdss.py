"""Import tasks for the Sloan Digital Sky Survey.
"""
import csv
import os
import re
from glob import glob

from astrocats.catalog.utils import pbar_strings


def do_sdss(catalog):
    task_str = catalog.get_current_task_str()
    with open(os.path.join(catalog.get_current_task_repo(),
                           'SDSS/2010ApJ...708..661D.txt'), 'r') as sdss_file:
        bibcodes2010 = sdss_file.read().split('\n')
    sdssbands = ['u', 'g', 'r', 'i', 'z']
    file_names = list(
        glob(os.path.join(catalog.get_current_task_repo(), 'SDSS/*.sum')))
    for fname in pbar_strings(file_names, task_str):
        tsvin = csv.reader(open(fname, 'r'), delimiter=' ',
                           skipinitialspace=True)
        basename = os.path.basename(fname)
        if basename in bibcodes2010:
            bibcode = '2010ApJ...708..661D'
        else:
            bibcode = '2008AJ....136.2306H'

        for rr, row in enumerate(tsvin):
            if rr == 0:
                if row[5] == 'RA:':
                    name = 'SDSS-II SN ' + row[3]
                else:
                    name = 'SN' + row[5]
                name = catalog.add_entry(name)
                source = catalog.entries[name].add_source(bibcode=bibcode)
                catalog.entries[name].add_quantity('alias', name, source)
                catalog.entries[name].add_quantity(
                    'alias', 'SDSS-II SN ' + row[3], source)

                if row[5] != 'RA:':
                    year = re.findall(r'\d+', name)[0]
                    catalog.entries[name].add_quantity('discoverdate', year,
                                                       source)

                catalog.entries[name].add_quantity(
                    'ra', row[-4], source, unit='floatdegrees')
                catalog.entries[name].add_quantity(
                    'dec', row[-2], source, unit='floatdegrees')
            if rr == 1:
                error = row[4] if float(row[4]) >= 0.0 else ''
                (catalog.entries[name]
                 .add_quantity('redshift', row[2], source,
                               error=error,
                               kind='heliocentric'))
            if rr >= 19:
                # Skip bad measurements
                if int(row[0]) > 1024:
                    continue

                mjd = row[1]
                band = sdssbands[int(row[2])]
                magnitude = row[3]
                e_mag = row[4]
                telescope = 'SDSS'
                (catalog.entries[name]
                 .add_photometry(time=mjd, telescope=telescope,
                                 band=band, magnitude=magnitude,
                                 e_magnitude=e_mag, source=source,
                                 system='SDSS'))

    catalog.journal_entries()
    return

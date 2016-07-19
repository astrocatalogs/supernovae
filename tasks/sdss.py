"""Import tasks for the Sloan Digital Sky Survey.
"""
import csv
import os
import re
from glob import glob

from astrocats.catalog.utils import pbar_strings

from ..supernova import SUPERNOVA


def do_sdss_photo(catalog):
    task_str = catalog.get_current_task_str()
    with open(os.path.join(catalog.get_current_task_repo(),
                           'SDSS/2010ApJ...708..661D.txt'), 'r') as sdss_file:
        bibcodes2010 = sdss_file.read().split('\n')
    sdssbands = ['u', 'g', 'r', 'i', 'z']
    file_names = (list(glob(os.path.join(catalog
                                         .get_current_task_repo(),
                                         'SDSS/sum/*.sum'))) +
                  list(glob(os.path.join(catalog
                                         .get_current_task_repo(),
                                         'SDSS/SMP_Data/*.dat'))))
    for fi, fname in enumerate(pbar_strings(file_names, task_str)):
        tsvin = csv.reader(open(fname, 'r'), delimiter=' ',
                           skipinitialspace=True)
        basename = os.path.basename(fname)
        hasred = True
        rst = 19
        if '.dat' in fname:
            bibcode = '2014arXiv1401.3317S'
            hasred = False
            rst = 4
        elif basename in bibcodes2010:
            bibcode = '2010ApJ...708..661D'
        else:
            bibcode = '2008AJ....136.2306H'

        for rr, row in enumerate(tsvin):
            if rr == 0:
                # Ignore IAU names from Sako 2014 as they are unreliable
                if row[5] == 'RA:' or bibcode == '2014arXiv1401.3317S':
                    name = 'SDSS-II SN ' + row[3]
                else:
                    name = 'SN' + row[5]
                name = catalog.add_entry(name)
                source = catalog.entries[name].add_source(bibcode=bibcode)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.ALIAS, name, source)
                catalog.entries[name].add_quantity(
                    SUPERNOVA.ALIAS, 'SDSS-II SN ' + row[3], source)

                if row[5] != 'RA:':
                    year = re.findall(r'\d+', name)[0]
                    catalog.entries[name].add_quantity(
                        SUPERNOVA.DISCOVER_DATE, year, source)

                catalog.entries[name].add_quantity(
                    SUPERNOVA.RA, row[-4], source, u_value='floatdegrees')
                catalog.entries[name].add_quantity(
                    SUPERNOVA.DEC, row[-2], source, u_value='floatdegrees')
            if hasred and rr == 1:
                error = row[4] if float(row[4]) >= 0.0 else ''
                (catalog.entries[name]
                 .add_quantity(SUPERNOVA.REDSHIFT, row[2], source,
                               e_value=error,
                               kind='heliocentric'))
            if rr >= rst:
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
        if not fi % 1000:
            catalog.journal_entries()

    catalog.journal_entries()
    return

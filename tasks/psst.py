"""Import tasks for the Pan-STARRS Survey for Transients
"""
import csv
import os

from astrocats.catalog.utils import make_date_string, pbar
from astropy.time import Time as astrotime

from ..supernova import SUPERNOVA


def do_psst(catalog):
    task_str = catalog.get_current_task_str()
    # 2016MNRAS.462.4094S
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2016MNRAS.462.4094S-tab1.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name, source) = catalog.new_entry(
                row[0], bibcode='2016MNRAS.462.4094S')
            catalog.entries[name].add_quantity(
                SUPERNOVA.CLAIMED_TYPE, row[3].replace('SN', '').strip('() '),
                source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                row[5].strip('() '),
                source,
                kind='spectroscopic')

    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2016MNRAS.462.4094S-tab2.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name, source) = catalog.new_entry(
                row[0], bibcode='2016MNRAS.462.4094S')
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
            mldt = astrotime(float(row[4]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                               discoverdate, source)

    catalog.journal_entries()

    # 2016ApJ...827L..40S
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2016ApJ...827L..40S.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            (name, source) = catalog.new_entry(
                row[0], bibcode='2016ApJ...827L..40S')
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
            mldt = astrotime(float(row[3]), format='mjd').datetime
            discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                               discoverdate, source)
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row[6],
                                               source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, row[7], source, kind='spectroscopic')
            for alias in [x.strip() for x in row[8].split(',')]:
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, alias,
                                                   source)

    catalog.journal_entries()

    return

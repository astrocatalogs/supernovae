"""Import tasks related to Fermi supernova remnants.
"""
import csv
import os

from astrocats.catalog.utils import pbar

from ..supernova import SUPERNOVA


def do_fermi(catalog):
    task_str = catalog.get_current_task_str()
    with open(os.path.join(catalog.get_current_task_repo(),
                           '1SC_catalog_v01.asc'), 'r') as ff:
        tsvin = list(csv.reader(ff, delimiter=','))
        for ri, row in enumerate(pbar(tsvin, task_str)):
            if row[0].startswith('#'):
                if len(row) > 1 and 'UPPER_LIMITS' in row[1]:
                    break
                continue
            if 'Classified' not in row[1]:
                continue
            name = row[0].replace('SNR', 'G')
            name = catalog.add_entry(name)
            source = (catalog.entries[name]
                      .add_source(bibcode='2016ApJS..224....8A'))
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.ALIAS, row[0].replace('SNR', 'MWSNR'), source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.RA, row[2], source, u_value='floatdegrees')
            catalog.entries[name].add_quantity(
                SUPERNOVA.DEC, row[3], source, u_value='floatdegrees')
    catalog.journal_entries()
    return

"""Import tasks for the Supernova Cosmology Project.
"""
import csv
import os

from astrocats.utils import pbar
from astrocats.structures.struct import QUANTITY
from ..supernova import SUPERNOVA


def do_scp(catalog):
    task_str = catalog.get_current_task_str()
    path = os.path.join(catalog.get_current_task_repo(), 'SCP09.csv')
    tsvin = list(csv.reader(open(path, 'r'), delimiter=','))
    url = 'http://supernova.lbl.gov/2009ClusterSurvey/'
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if ri == 0:
            continue
        name = row[0].replace('SCP', 'SCP-')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(name='Supernova Cosmology Project', url=url)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if row[1]:
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)
        if row[2]:
            kind = 'spectroscopic' if row[3] == 'sn' else SUPERNOVA.HOST
            catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[2], source, kind=kind)
        if row[4]:
            catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[4], source, kind='cluster')
        if row[6]:
            claimedtype = row[6].replace('SN ', '')
            if claimedtype == '?':
                continue

            if 'a' in row[7] and 'c' in row[7]:
                quant = {QUANTITY.KIND: 'spectroscopic/light curve'}
            elif 'a' in row[7]:
                quant = {QUANTITY.KIND: 'spectroscopic'}
            elif 'c' in row[7]:
                quant = {QUANTITY.KIND: 'light curve'}
            else:
                quant = {}

            catalog.entries[name].add_quantity(
                SUPERNOVA.CLAIMED_TYPE, claimedtype, source, **quant)

    catalog.journal_entries()
    return

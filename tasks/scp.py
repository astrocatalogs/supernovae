"""Import tasks for the Supernova Cosmology Project.
"""
import csv
import os

from astrocats.catalog.utils import pbar

from ..supernova import SUPERNOVA


def do_scp(catalog):
    task_str = catalog.get_current_task_str()
    tsvin = list(csv.reader(open(
        os.path.join(catalog.get_current_task_repo(), 'SCP09.csv'), 'r'),
        delimiter=','))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if ri == 0:
            continue
        name = row[0].replace('SCP', 'SCP-')
        name = catalog.add_entry(name)
        source = (catalog.entries[name]
                  .add_source(name='Supernova Cosmology Project',
                              url=('http://supernova.lbl.gov/'
                                   '2009ClusterSurvey/')))
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if row[1]:
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)
        if row[2]:
            kind = 'spectroscopic' if row[3] == 'sn' else SUPERNOVA.HOST
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, row[2], source, kind=kind)
        if row[4]:
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, row[2], source, kind='cluster')
        if row[6]:
            claimedtype = row[6].replace('SN ', '')
            kind = ('spectroscopic/light curve' if 'a' in row[7] and 'c' in
                    row[7] else
                    'spectroscopic' if 'a' in row[7] else
                    'light curve' if 'c' in row[7]
                    else '')
            if claimedtype != '?':
                catalog.entries[name].add_quantity(
                    SUPERNOVA.CLAIMED_TYPE, claimedtype, source, kind=kind)

    catalog.journal_entries()
    return

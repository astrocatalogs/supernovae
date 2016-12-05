"""Import tasks for the PESSTO spectroscopic program.
"""
import csv
import os

from astrocats.catalog.utils import pbar
from astrocats.catalog.photometry import PHOTOMETRY

from ..supernova import SUPERNOVA


def do_pessto(catalog):
    task_str = catalog.get_current_task_str()
    pessto_path = os.path.join(
        catalog.get_current_task_repo(), 'PESSTO_MPHOT.csv')
    tsvin = list(csv.reader(open(pessto_path, 'r'), delimiter=','))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if ri == 0:
            bands = [xx.split('_')[0] for xx in row[3::2]]
            systems = [xx.split('_')[1].capitalize().replace(
                'Ab', 'AB') for xx in row[3::2]]
            continue
        name = row[1]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015A&A...579A..40S')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for hi, ci in enumerate(range(3, len(row) - 1, 2)):
            if not row[ci]:
                continue
            if systems[hi] == 'Swift':
                teles = 'Swift'
                instrument = 'UVOT'
                bandset = 'Swift'
            else:
                teles = 'NTT'
                instrument = 'EFOSC'
                bandset = 'Johnson'
            photodict = {
                PHOTOMETRY.TIME: row[2],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: row[ci],
                PHOTOMETRY.E_MAGNITUDE: row[ci + 1],
                PHOTOMETRY.BAND: bands[hi],
                PHOTOMETRY.SYSTEM: systems[hi],
                PHOTOMETRY.BAND_SET: bandset,
                PHOTOMETRY.TELESCOPE: teles,
                PHOTOMETRY.INSTRUMENT: instrument,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return

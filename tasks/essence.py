'''Import tasks for ESSENCE.
'''
import csv
import os
from glob import glob
from math import log10

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import pbar, pretty_num

from ..supernova import SUPERNOVA


def do_essence_photo(catalog):
    task_str = catalog.get_current_task_str()
    ess_path = os.path.join(catalog.get_current_task_repo(), 'ESSENCE',
                            'obj_table.dat')
    data = list(
        csv.reader(
            open(ess_path, 'r'),
            delimiter=' ',
            quotechar='"',
            skipinitialspace=True))
    for row in pbar(data, task_str):
        etype = row[2]
        if etype.upper().replace('?', '') in catalog.nonsnetypes:
            continue
        ess_name = 'ESSENCE ' + row[0]
        name, source = catalog.new_entry(
            ess_name, bibcode='2016ApJS..224....3N')
        if row[1] != '---':
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, 'SN' + row[1],
                                               source)
        if etype != '---':
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, etype,
                                               source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[5], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row[11], source, kind='host', e_value=row[12])

    files = glob(
        os.path.join(catalog.get_current_task_repo(), 'ESSENCE',
                     '*clean*.dat'))

    # Still written for SNLS
    for pfile in pbar(files, task_str):
        name = 'ESSENCE ' + pfile.split('/')[-1].split('.')[0]
        name, source = catalog.new_entry(name, bibcode='2016ApJS..224....3N')
        with open(pfile, 'r') as f:
            rows = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
        for ri, row in enumerate(rows):
            if ri == 1:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    row[5],
                    source,
                    kind=['spectroscopic', 'heliocentric'])
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    row[6],
                    source,
                    kind=['spectroscopic', 'cmb'])
                continue
            if row[0].startswith('#'):
                continue
            counts = row[3]
            lerr = row[4]
            uerr = row[5]
            # Being extra strict here with the flux constraint.
            if float(counts) < 3.0 * float(lerr):
                continue
            sig = 5
            magnitude = pretty_num(25.0 - 2.5 * log10(float(counts)), sig=sig)
            e_l_mag = pretty_num(
                2.5 * log10(float(counts) / (float(counts) - float(lerr))),
                sig=sig)
            e_u_mag = pretty_num(
                2.5 * log10(1.0 + float(uerr) / float(counts)), sig=sig)
            photodict = {
                PHOTOMETRY.TIME: row[1],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: row[2][0],
                PHOTOMETRY.MAGNITUDE: magnitude,
                PHOTOMETRY.E_LOWER_MAGNITUDE: e_l_mag,
                PHOTOMETRY.E_UPPER_MAGNITUDE: e_u_mag,
                PHOTOMETRY.COUNTS: counts,
                PHOTOMETRY.E_LOWER_COUNTS: lerr,
                PHOTOMETRY.E_UPPER_COUNTS: uerr,
                PHOTOMETRY.ZERO_POINT: '25.0',
                PHOTOMETRY.SOURCE: source,
                PHOTOMETRY.TELESCOPE: 'CTIO 4m',
                PHOTOMETRY.SYSTEM: 'Natural'
            }
            catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return

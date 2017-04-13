"""Import tasks for the Gamma-ray Bursts Catalog.
"""
import csv
import os

from astropy.time import Time as astrotime

from astrocats.catalog.utils import make_date_string, pbar
from decimal import Decimal

from ..supernova import SUPERNOVA


def do_grb(catalog):
    task_str = catalog.get_current_task_str()
    file_path = os.path.join(catalog.get_current_task_repo(),
                             'GRB-catalog/catalog.csv')
    csvtxt = catalog.load_url('http://www.grbcatalog.org/'
                              'download_data?cut_0_min=3&cut_0=BAT%20T90'
                              '&cut_0_max=100000&num_cuts=1&no_date_cut=True',
                              file_path)
    if not csvtxt:
        return
    csvtxt = csvtxt.replace('\x0C', '').splitlines()
    data = list(
        csv.reader(
            csvtxt, delimiter=',', quotechar='"', skipinitialspace=True))
    for r, row in enumerate(pbar(data, task_str)):
        if r == 0:
            continue
        (name, source) = catalog.new_entry(
            'GRB ' + row[0],
            srcname='Gamma-ray Bursts Catalog',
            url='http://www.grbcatalog.org')
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row[2], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row[3], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'LGRB',
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[8], source)

    catalog.journal_entries()
    return


def do_batse(catalog):
    task_str = catalog.get_current_task_str()
    file_path = os.path.join(catalog.get_current_task_repo(),
                             'BATSE/basic_table.txt')
    csvtxt = catalog.load_url(
        'http://gammaray.nsstc.nasa.gov/batse/grb/catalog/current/tables/'
        'basic_table.txt', file_path)
    if not csvtxt:
        return
    data = list(
        csv.reader(
            csvtxt.splitlines(),
            delimiter=' ',
            quotechar='"',
            skipinitialspace=True))

    file_path = os.path.join(catalog.get_current_task_repo(),
                             'BATSE/duration_table.txt')
    csvtxt = catalog.load_url(
        'http://gammaray.nsstc.nasa.gov/batse/grb/catalog/current/tables/'
        'duration_table.txt', file_path)
    if not csvtxt:
        return
    data2 = list(
        csv.reader(
            csvtxt.splitlines(),
            delimiter=' ',
            quotechar='"',
            skipinitialspace=True))
    t90s = {}
    for row in data2:
        # Add one sigma to quoted T90 to compare to
        t90s[row[0]] = float(row[-3]) + float(row[-2])

    prev_oname = ''
    grb_letter = 'A'
    for r, row in enumerate(pbar(data, task_str)):
        if row[0].startswith('#'):
            continue
        oname = 'GRB ' + row[2]
        if oname.replace('-', '') == prev_oname:
            grb_letter = chr(ord(grb_letter) + 1)
        else:
            grb_letter = 'A'
        prev_oname = oname.replace('-', '')
        if oname.endswith('-'):
            oname = oname.replace('-', grb_letter)
        if row[-1] == 'Y':
            continue
        if row[0] not in t90s or t90s[row[0]] < 3.0:
            continue
        (name, source) = catalog.new_entry(
            oname,
            srcname='BATSE Catalog',
            bibcode='1999ApJS..122..465P',
            url='http://gammaray.nsstc.nasa.gov/batse/grb/catalog/')

        jd = Decimal(2440000.5) + Decimal(row[3])
        astrot = astrotime(float(jd), format='jd').datetime
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE,
            make_date_string(astrot.year, astrot.month, astrot.day), source)
        pos_err = str(Decimal(row[9]) * Decimal(3600))
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA,
            row[5],
            source,
            u_value='floatdegrees',
            e_value=pos_err)
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC,
            row[6],
            source,
            u_value='floatdegrees',
            e_value=pos_err)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'LGRB',
                                           source)

    catalog.journal_entries()
    return

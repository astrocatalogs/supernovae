"""Import tasks for the Sloan Digital Sky Survey.
"""
import csv
import os
import re
from glob import glob

from astropy.coordinates import SkyCoord as coord
from astropy.time import Time as astrotime

from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.utils import make_date_string, pbar, pbar_strings
from cdecimal import Decimal

from ..supernova import SUPERNOVA


def do_sdss_photo(catalog):
    task_str = catalog.get_current_task_str()
    # Load up metadata first
    with open(os.path.join(catalog.get_current_task_repo(),
                           'SDSS/sdsssn_master.dat2'), 'r') as f:
        rows = list(csv.reader(f.read().splitlines()[1:], delimiter=' '))
        ignored_cids = []
        columns = {
            SUPERNOVA.RA: 1,
            SUPERNOVA.DEC: 2,
            SUPERNOVA.ALIAS: 4,
            SUPERNOVA.CLAIMED_TYPE: 5,
            SUPERNOVA.REDSHIFT: 11,
            SUPERNOVA.MAX_DATE: 21,
            SUPERNOVA.HOST_RA: 99,
            SUPERNOVA.HOST_DEC: 100
        }
        colnums = {v: k for k, v in columns.items()}

        rows = [[x.replace('\\N', '') for x in y] for y in rows]

        co = [[x[0], x[99], x[100]] for x in rows if x[99] and x[100]]
        coo = coord([x[1] for x in co], [x[2] for x in co], unit="deg")
        coo = [''.join([y[:9] for y in x.split()]) for x in
               coo.to_string('hmsdms', sep='')]
        hostdict = dict(zip([x[0] for x in co],
                            ['SDSS J' + x[1:] for x in coo]))

        for ri, row in enumerate(pbar(rows, task_str + ": metadata")):
            name = ''

            # Check if type is non-SNe first
            ct = row[columns[SUPERNOVA.CLAIMED_TYPE]]
            al = row[columns[SUPERNOVA.ALIAS]]
            if ct in ['AGN', 'Variable'] and not al:
                catalog.log.info('`{}` is not a SN, not '
                                 'adding.'.format(row[0]))
                ignored_cids.append(row[0])
                continue

            # Add entry
            (name, source) = catalog.new_entry(
                'SDSS-II SN ' + row[0], bibcode='2014arXiv1401.3317S',
                url='http://data.sdss3.org/sas/dr10/boss/papers/supernova/')

            # Add host name
            if row[0] in hostdict:
                catalog.entries[name].add_quantity(SUPERNOVA.HOST,
                                                   hostdict[row[0]], source)

            # Add other metadata
            for cn in colnums:
                key = colnums[cn]
                if not key:
                    continue
                ic = int(cn)
                val = row[ic]
                if not val:
                    continue
                kwargs = {}
                if key == SUPERNOVA.ALIAS:
                    val = 'SN' + val
                elif key in [SUPERNOVA.RA, SUPERNOVA.DEC, SUPERNOVA.HOST_RA,
                             SUPERNOVA.HOST_DEC]:
                    kwargs = {QUANTITY.U_VALUE: 'floatdegrees'}
                    if key in [SUPERNOVA.RA, SUPERNOVA.HOST_RA]:
                        fval = float(val)
                        if fval < 0.0:
                            val = str(Decimal(360) + Decimal(fval))
                elif key == SUPERNOVA.CLAIMED_TYPE:
                    val = val.lstrip('pz').replace('SN', '')
                elif key == SUPERNOVA.REDSHIFT:
                    kwargs[QUANTITY.KIND] = 'spectroscopic'
                    if float(row[ic + 1]) > 0.0:
                        kwargs[QUANTITY.E_VALUE] = row[ic + 1]
                elif key == SUPERNOVA.MAX_DATE:
                    dt = astrotime(float(val), format='mjd').datetime
                    val = make_date_string(dt.year, dt.month, dt.day)
                catalog.entries[name].add_quantity(key, val, source, **kwargs)

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

        skip_entry = False
        for rr, row in enumerate(tsvin):
            if skip_entry:
                break
            if rr == 0:
                # Ignore non-SNe objects and those not in metadata table above
                if row[3] in ignored_cids:
                    skip_entry = True
                    continue
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

                if row[5] != 'RA:' and bibcode == '2014arXiv1401.3317S':
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

"""Import tasks for data directly donated to the Open Supernova Catalog.
"""
import csv
import json
import os
from glob import glob
from math import isnan

from astrocats.catalog.utils import is_number, pbar, pbar_strings, rep_chars


def do_donations(catalog):
    task_str = catalog.get_current_task_str()
    # Nicholl 04-01-16 donation
    with open(os.path.join(catalog.get_current_task_repo(),
                           'Nicholl-04-01-16/bibcodes.json'), 'r') as f:
        bcs = json.loads(f.read())

    file_names = glob(os.path.join(
        catalog.get_current_task_repo(), 'Nicholl-04-01-16/*.txt'))
    for datafile in pbar_strings(file_names, task_str +
                                 ': Nicholl-04-01-16'):
        inpname = os.path.basename(datafile).split('_')[0]
        name = catalog.add_entry(inpname)
        bibcode = ''
        for bc in bcs:
            if inpname in bcs[bc]:
                bibcode = bc
        if not bibcode:
            raise ValueError('Bibcode not found!')
        source = catalog.entries[name].add_source(bibcode=bibcode)
        catalog.entries[name].add_quantity('alias', inpname, source)
        with open(datafile, 'r') as f:
            tsvin = csv.reader(f, delimiter='\t', skipinitialspace=True)
            for r, rrow in enumerate(tsvin):
                row = list(filter(None, rrow))
                if not row:
                    continue
                if row[0][0] == '#' and row[0] != '#MJD':
                    continue
                if row[0] == '#MJD':
                    bands = [x for x in row[1:] if x and 'err' not in x]
                    continue
                mjd = row[0]
                if not is_number(mjd):
                    continue
                for v, val in enumerate(row[1::2]):
                    upperlimit = ''
                    if '>' in val:
                        upperlimit = True
                    mag = val.strip('>')
                    if (not is_number(mag) or isnan(float(mag)) or
                            float(mag) > 90.0):
                        continue
                    err = ''
                    if (is_number(row[2 * v + 2]) and
                            not isnan(float(row[2 * v + 2]))):
                        err = row[2 * v + 2]
                    catalog.entries[name].add_photometry(
                        time=mjd, band=bands[v], magnitude=mag,
                        e_magnitude=err, upperlimit=upperlimit, source=source)
    catalog.journal_entries()

    # Maggi 04-11-16 donation (MC SNRs)
    with open(os.path.join(catalog.get_current_task_repo(),
                           'Maggi-04-11-16/LMCSNRs_OpenSNe.csv')) as f:
        tsvin = csv.reader(f, delimiter=',')
        for row in pbar(list(tsvin), task_str +
                        ': Maggi-04-11-16/LMCSNRs'):
            name = 'MCSNR ' + row[0]
            name = catalog.add_entry(name)
            ra = row[2]
            dec = row[3]
            source = (catalog.entries[name]
                      .add_source(bibcode='2016A&A...585A.162M'))
            catalog.entries[name].add_quantity(
                'alias', 'LMCSNR J' + rep_chars(ra, ' :.') +
                rep_chars(dec, ' :.'), source)
            catalog.entries[name].add_quantity('alias', name, source)
            if row[1] != 'noname':
                catalog.entries[name].add_quantity('alias', row[1], source)
            catalog.entries[name].add_quantity('ra', row[2], source)
            catalog.entries[name].add_quantity('dec', row[3], source)
            catalog.entries[name].add_quantity('host', 'LMC', source)
            if row[4] == '1':
                catalog.entries[name].add_quantity('claimedtype', 'Ia', source)
            elif row[4] == '2':
                catalog.entries[name].add_quantity('claimedtype', 'CC', source)
    with open(os.path.join(catalog.get_current_task_repo(),
                           'Maggi-04-11-16/SMCSNRs_OpenSNe.csv')) as f:
        tsvin = csv.reader(f, delimiter=',')
        for row in pbar(list(tsvin), task_str +
                        ': Maggi-04-11-16/SMCSNRs'):
            name = 'MCSNR ' + row[0]
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_source(name='Pierre Maggi')
            ra = row[3]
            dec = row[4]
            catalog.entries[name].add_quantity(
                name, 'alias', 'SMCSNR J' + ra.replace(':', '')[:6] +
                dec.replace(':', '')[:7], source)
            catalog.entries[name].add_quantity('alias', name, source)
            catalog.entries[name].add_quantity('alias', row[1], source)
            catalog.entries[name].add_quantity('alias', row[2], source)
            catalog.entries[name].add_quantity('ra', row[3], source)
            catalog.entries[name].add_quantity('dec', row[4], source)
            catalog.entries[name].add_quantity('host', 'SMC', source)
    catalog.journal_entries()

    # Galbany 04-18-16 donation
    folders = next(os.walk(os.path.join(
        catalog.get_current_task_repo(), 'galbany-04-18-16/')))[1]
    bibcode = '2016AJ....151...33G'
    for folder in folders:
        infofiles = glob(os.path.join(catalog.get_current_task_repo(),
                                      'galbany-04-18-16/') + folder +
                         '/*.info')
        photfiles = glob(os.path.join(catalog.get_current_task_repo(),
                                      'galbany-04-18-16/') + folder +
                         '/*.out*')

        zhel = ''
        zcmb = ''
        zerr = ''
        for path in infofiles:
            with open(path, 'r') as f:
                lines = f.read().splitlines()
                for line in lines:
                    splitline = line.split(':')
                    field = splitline[0].strip().lower()
                    value = splitline[1].strip()
                    if field == 'name':
                        name = value[:6].upper()
                        name += (value[6].upper() if len(value) == 7
                                 else value[6:])
                        name = catalog.add_entry(name)
                        source = (catalog.entries[name]
                                  .add_source(bibcode=bibcode))
                        catalog.entries[name].add_quantity('alias', name,
                                                           source)
                    elif field == 'type':
                        claimedtype = value.replace('SN', '')
                        catalog.entries[name].add_quantity(
                            'claimedtype', claimedtype, source)
                    elif field == 'zhel':
                        zhel = value
                    elif field == 'redshift_error':
                        zerr = value
                    elif field == 'zcmb':
                        zcmb = value
                    elif field == 'ra':
                        catalog.entries[name].add_quantity(
                            'ra', value, source, unit='floatdegrees')
                    elif field == 'dec':
                        catalog.entries[name].add_quantity(
                            'dec', value, source, unit='floatdegrees')
                    elif field == 'host':
                        value = value.replace('- ', '-').replace('G ', 'G')
                        catalog.entries[name].add_quantity('host', value,
                                                           source)
                    elif field == 'e(b-v)_mw':
                        catalog.entries[name].add_quantity(
                            'ebv', value, source)

        catalog.entries[name].add_quantity(
            'redshift', zhel, source, error=zerr, kind='heliocentric')
        catalog.entries[name].add_quantity(
            'redshift', zcmb, source, error=zerr, kind='cmb')

        for path in photfiles:
            with open(path, 'r') as f:
                band = ''
                lines = f.read().splitlines()
                for li, line in enumerate(lines):
                    if li in [0, 2, 3]:
                        continue
                    if li == 1:
                        band = line.split(':')[-1].strip()
                    else:
                        cols = list(filter(None, line.split()))
                        if not cols:
                            continue
                        catalog.entries[name].add_photometry(
                            time=cols[0], magnitude=cols[1],
                            e_magnitude=cols[2],
                            band=band, system=cols[3], telescope=cols[4],
                            source=source)
    catalog.journal_entries()

    # Brown 05-14-16
    files = glob(os.path.join(
        catalog.get_current_task_repo(), 'brown-05-14-16/*.dat'))
    for fi in pbar(files, task_str):
        name = os.path.basename(fi).split('_')[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            name='Swift Supernovae', bibcode='2014Ap&SS.354...89B',
            url='http://people.physics.tamu.edu/pbrown/SwiftSN/swift_sn.html')
        catalog.entries[name].add_quantity('alias', name, source)
        with open(fi, 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                if not line or line[0] == '#':
                    continue
                cols = list(filter(None, line.split()))
                band = cols[0]
                mjd = cols[1]
                # Skip lower limit entries for now
                if cols[2] == 'NULL' and cols[6] == 'NULL':
                    continue
                isupp = cols[2] == 'NULL' and cols[6] != 'NULL'
                mag = cols[2] if not isupp else cols[4]
                e_mag = cols[3] if not isupp else ''
                upp = '' if not isupp else True
                (catalog.entries[name]
                 .add_photometry(time=mjd, magnitude=mag,
                                 e_magnitude=e_mag,
                                 upperlimit=upp, band=band, source=source,
                                 telescope='Swift', instrument='UVOT',
                                 system='Vega'))
    catalog.journal_entries()

    # Nicholl 05-03-16
    files = glob(os.path.join(
        catalog.get_current_task_repo(), 'nicholl-05-03-16/*.txt'))
    name = catalog.add_entry('SN2015bn')
    source = catalog.entries[name].add_source(bibcode='2016arXiv160304748N')
    catalog.entries[name].add_quantity('alias', name, source)
    catalog.entries[name].add_quantity('alias', 'PS15ae', source)
    for fi in pbar(files, task_str):
        telescope = os.path.basename(fi).split('_')[1]
        with open(fi, 'r') as f:
            lines = f.read().splitlines()
            for li, line in enumerate(lines):
                if not line or (line[0] == '#' and li != 0):
                    continue
                cols = list(filter(None, line.split()))
                if not cols:
                    continue
                if li == 0:
                    bands = cols[1:]
                    continue

                mjd = cols[0]
                for ci, col in enumerate(cols[1::2]):
                    if not is_number(col):
                        continue

                    emag = cols[2 * ci + 2]
                    upp = ''
                    if not is_number(emag):
                        emag = ''
                        upp = True
                    instrument = 'UVOT' if telescope == 'Swift' else ''
                    (catalog.entries[name]
                     .add_photometry(time=mjd, magnitude=col,
                                     e_magnitude=emag, upperlimit=upp,
                                     band=bands[ci], source=source,
                                     telescope=telescope,
                                     instrument=instrument,
                                     system='Vega' if
                                     telescope == 'Swift' else 'AB'))

    catalog.journal_entries()
    return

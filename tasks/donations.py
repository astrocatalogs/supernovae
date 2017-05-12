"""Import tasks for data directly donated to the Open Supernova Catalog."""
import csv
import json
import os
from decimal import Decimal
from glob import glob
from math import floor, isnan

import numpy as np
from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import (get_sig_digits, is_number, jd_to_mjd,
                                     pbar, pbar_strings, pretty_num, rep_chars)
from astropy.io.ascii import read
from astropy.time import Time as astrotime

from ..supernova import SUPERNOVA


def do_donated_photo(catalog):
    """Import donated photometry."""
    task_str = catalog.get_current_task_str()

    # Private donations here #
    if not catalog.args.travis:
        pass
    # End private donations #

    # Ponder 05-12-17 donation
    with open(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Ponder-05-12-17', 'meta.json'), 'r') as f:
        metadict = json.loads(f.read())
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Ponder-05-12-17', '*.dat'))
    for path in file_names:
        with open(path, 'r') as f:
            tsvin = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
        oname = path.split('/')[-1].split('.')[0]
        name, source = catalog.new_entry(
            oname, bibcode=metadict[oname]['bibcode'])
        for row in pbar(tsvin, task_str + ': Ponder ' + oname):
            if row[0][0] == '#' or not is_number(row[-1]):
                continue
            mjd = row[1]
            bandinst = row[2].split('_')
            band = bandinst[0]
            inst = ''
            if len(bandinst) > 1:
                inst = bandinst[1]
            mag = row[3]
            uerr = row[4]
            lerr = row[5]
            photodict = {
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_LOWER_MAGNITUDE: lerr,
                PHOTOMETRY.E_UPPER_MAGNITUDE: uerr,
                PHOTOMETRY.SOURCE: source
            }
            if inst:
                photodict[PHOTOMETRY.INSTRUMENT] = inst
            catalog.entries[name].add_photometry(**photodict)

    # Benetti 03-08-17 donation
    path = os.path.join(catalog.get_current_task_repo(), 'Donations',
                        'Benetti-03-08-17', '1999E.dat')
    with open(path, 'r') as f:
        tsvin = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
        name, source = catalog.new_entry(
            'SN1999E', bibcode='2003MNRAS.340..191R')
        bands = None
        for row in tsvin:
            if not row or row[0][0] == '#':
                continue
            if not bands:
                bands = row[2:-2]
                continue
            mjd = row[1]
            tel = row[-1] if 'IAUC' not in row[-1] else None
            for bi, band in enumerate(bands):
                mag = row[2 + 2 * bi]
                if mag == '9999':
                    continue
                err = row[2 + 2 * bi + 1]
                limit = row[6] == 'True'
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.TELESCOPE: tel,
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: mag,
                    PHOTOMETRY.SOURCE: source
                }
                if err != '.00':
                    photodict[PHOTOMETRY.E_MAGNITUDE] = str(Decimal(err))
                if tel:
                    photodict[PHOTOMETRY.TELESCOPE] = tel
                catalog.entries[name].add_photometry(**photodict)

    # Nicholl 01-29-17 donation
    with open(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Nicholl-01-29-17', 'meta.json'), 'r') as f:
        metadict = json.loads(f.read())
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Nicholl-01-29-17', '*.txt'))
    for path in file_names:
        data = read(path, format='cds')
        oname = path.split('/')[-1].split('_')[0]
        name, source = catalog.new_entry(
            oname, bibcode=metadict[oname]['bibcode'])
        for row in pbar(data, task_str + ': Nicholl ' + oname):
            photodict = {
                PHOTOMETRY.TIME: str(row['MJD']),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: str(row['mag']),
                PHOTOMETRY.BAND: row['Filter'],
                PHOTOMETRY.SOURCE: source
            }
            if 'system' in metadict[oname]:
                photodict[PHOTOMETRY.SYSTEM] = metadict[oname]['system']
            if 'l_mag' in row.columns and row['l_mag'] == '>':
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            elif 'e_mag' in row.columns:
                photodict[PHOTOMETRY.E_MAGNITUDE] = str(row['e_mag'])
            if 'Telescope' in row.columns:
                photodict[PHOTOMETRY.TELESCOPE] = row['Telescope']
            catalog.entries[name].add_photometry(**photodict)

    # Arcavi 2016gkg donation
    path = os.path.join(catalog.get_current_task_repo(), 'Donations',
                        'Arcavi-01-24-17', 'SN2016gkg.txt')
    with open(path, 'r') as f:
        tsvin = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
        name, source = catalog.new_entry(
            'SN2016gkg', bibcode='2016arXiv161106451A')
        for row in tsvin:
            if row[0][0] == '#':
                continue
            mjd = str(jd_to_mjd(Decimal(row[0])))
            tel = row[1]
            band = row[3]
            mag = row[4]
            err = row[5]
            limit = row[6] == 'True'
            photodict = {
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TELESCOPE: tel,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.SOURCE: source
            }
            if limit:
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            else:
                photodict[PHOTOMETRY.E_MAGNITUDE] = err
            catalog.entries[name].add_photometry(**photodict)

    # Nicholl Gaia16apd donation
    path = os.path.join(catalog.get_current_task_repo(), 'Donations',
                        'Nicholl-01-20-17', 'gaia16apd_phot.txt')

    data = read(path, format='cds')
    name, source = catalog.new_entry(
        'Gaia16apd', bibcode='2017ApJ...835L...8N')
    for row in pbar(data, task_str + ': Nicholl Gaia16apd'):
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: str(row['mag']),
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.TELESCOPE: row['Telescope'],
            PHOTOMETRY.SOURCE: source
        }
        if row['l_mag'] == '>':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = str(row['e_mag'])
        catalog.entries[name].add_photometry(**photodict)

    # Kuncarayakti-01-09-17
    datafile = os.path.join(catalog.get_current_task_repo(), 'Donations',
                            'Kuncarayakti-01-09-17', 'SN1978K.dat')
    inpname = os.path.basename(datafile).split('.')[0]
    with open(datafile, 'r') as f:
        tsvin = csv.reader(f, delimiter=' ', skipinitialspace=True)
        host = False
        for ri, row in enumerate(tsvin):
            if ri == 0:
                continue
            if row[0][0] == '#':
                rsplit = [x.strip('# ') for x in ' '.join(row).split(',')]
                bc = rsplit[0]
                tel, ins = '', ''
                if len(rsplit) > 1:
                    tel = rsplit[1]
                if len(rsplit) > 2:
                    ins = rsplit[2]
                continue
            (name, source) = catalog.new_entry(inpname, bibcode=bc)
            mag = row[4]
            err = row[5]
            mjd = str(astrotime('-'.join(row[:3]), format='iso').mjd)
            photodict = {
                PHOTOMETRY.BAND: row[3],
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag.strip('>s'),
                PHOTOMETRY.SOURCE: source
            }
            if is_number(err):
                photodict[PHOTOMETRY.E_MAGNITUDE] = err
            if tel:
                photodict[PHOTOMETRY.TELESCOPE] = tel
            if ins:
                photodict[PHOTOMETRY.INSTRUMENT] = ins
            if '>' in mag:
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            if 's' in mag:
                photodict[PHOTOMETRY.SYNTHETIC] = True
            catalog.entries[name].add_photometry(**photodict)

    # Nugent 01-09-17 donation
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Nugent-01-09-17', '*.dat'))
    for datafile in pbar_strings(file_names, task_str + ': Nugent-01-09-17'):
        inpname = os.path.basename(datafile).split('.')[0]
        (name, source) = catalog.new_entry(
            inpname, bibcode='2006ApJ...645..841N')
        with open(datafile, 'r') as f:
            tsvin = csv.reader(f, delimiter=' ', skipinitialspace=True)
            host = False
            for urow in tsvin:
                row = list(filter(None, urow))
                counts = row[2]
                e_counts = row[3]
                zp = row[4]
                photodict = {
                    PHOTOMETRY.BAND: row[1],
                    PHOTOMETRY.TIME: row[0],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.COUNT_RATE: counts,
                    PHOTOMETRY.E_COUNT_RATE: e_counts,
                    PHOTOMETRY.ZERO_POINT: zp,
                    PHOTOMETRY.TELESCOPE: 'CFHT',
                    PHOTOMETRY.SURVEY: 'SNLS',
                    PHOTOMETRY.SOURCE: source
                }
                set_pd_mag_from_counts(photodict, counts, ec=e_counts, zp=zp)
                catalog.entries[name].add_photometry(**photodict)

    # Inserra 09-04-16 donation
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Inserra-09-04-16', '*.txt'))
    for datafile in pbar_strings(file_names, task_str + ': Inserra-09-04-16'):
        inpname = os.path.basename(datafile).split('.')[0]
        (name, source) = catalog.new_entry(
            inpname, bibcode='2013ApJ...770..128I')
        with open(datafile, 'r') as f:
            tsvin = csv.reader(f, delimiter=' ', skipinitialspace=True)
            host = False
            for row in tsvin:
                if row[0][0] == '#':
                    if row[0] == '#Host':
                        host = True
                        continue
                    host = False
                    bands = row[3:-1]
                    continue
                for bi, ba in enumerate(bands):
                    mag = row[5 + 2 * bi]
                    if not is_number(mag):
                        continue
                    system = 'AB'
                    if ba in ['U', 'B', 'V', 'R', 'I', 'J', 'H', 'K']:
                        system = 'Vega'
                    photodict = {
                        PHOTOMETRY.TIME: row[3],
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.BAND: ba,
                        PHOTOMETRY.MAGNITUDE: mag.strip('< '),
                        PHOTOMETRY.SOURCE: source,
                        PHOTOMETRY.SYSTEM: system
                    }
                    if 'ATel' not in row[-1]:
                        photodict[PHOTOMETRY.TELESCOPE] = row[-1]
                    if host:
                        photodict[PHOTOMETRY.HOST] = True
                    if '<' in mag:
                        photodict[PHOTOMETRY.UPPER_LIMIT] = True
                    e_mag = row[5 + 2 * bi + 1].strip('() ')
                    if is_number(e_mag):
                        photodict[PHOTOMETRY.E_MAGNITUDE] = e_mag
                    catalog.entries[name].add_photometry(**photodict)

    # Nicholl 04-01-16 donation
    with open(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Nicholl-04-01-16', 'bibcodes.json'), 'r') as f:
        bcs = json.loads(f.read())

    kcorrected = ['SN2011ke', 'SN2011kf', 'SN2012il', 'PTF10hgi', 'PTF11rks']
    ignorephoto = ['PTF10hgi', 'PTF11rks', 'SN2011ke', 'SN2011kf', 'SN2012il']

    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Nicholl-04-01-16/*.txt'))
    for datafile in pbar_strings(file_names, task_str + ': Nicholl-04-01-16'):
        inpname = os.path.basename(datafile).split('_')[0]
        isk = inpname in kcorrected
        name = catalog.add_entry(inpname)
        bibcode = ''
        for bc in bcs:
            if inpname in bcs[bc]:
                bibcode = bc
        if not bibcode:
            raise ValueError('Bibcode not found!')
        source = catalog.entries[name].add_source(bibcode=bibcode)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, inpname, source)
        if inpname in ignorephoto:
            continue
        with open(datafile, 'r') as f:
            tsvin = csv.reader(f, delimiter='\t', skipinitialspace=True)
            rtelescope = ''
            for r, rrow in enumerate(tsvin):
                row = list(filter(None, rrow))
                if not row:
                    continue
                if row[0] == '#MJD':
                    bands = [x for x in row[1:] if x and 'err' not in x]
                elif row[0][0] == '#' and len(row[0]) > 1:
                    rtelescope = row[0][1:]
                if row[0][0] == '#':
                    continue
                mjd = row[0]
                if not is_number(mjd):
                    continue
                for v, val in enumerate(row[1::2]):
                    upperlimit = ''
                    mag = val.strip('>')
                    emag = row[2 * v + 2]
                    if '>' in val or (is_number(emag) and float(emag) == 0.0):
                        upperlimit = True
                    if (not is_number(mag) or isnan(float(mag)) or
                            float(mag) > 90.0):
                        continue
                    band = bands[v]
                    instrument = ''
                    survey = ''
                    system = ''
                    telescope = rtelescope
                    if telescope == 'LSQ':
                        instrument = 'QUEST'
                    elif telescope == 'PS1':
                        instrument = 'GPC'
                    elif telescope == 'NTT':
                        instrument = 'EFOSC'
                    elif telescope == 'GROND':
                        instrument = 'GROND'
                        telescope = 'MPI/ESO 2.2m'
                    else:
                        if band == 'NUV':
                            instrument = 'GALEX'
                            telescope = 'GALEX'
                        elif band in ['u', 'g', 'r', 'i', 'z']:
                            if inpname.startswith('PS1'):
                                instrument = 'GPC'
                                telescope = 'PS1'
                                survey = 'Pan-STARRS'
                            elif inpname.startswith('PTF'):
                                telescope = 'P60'
                                survey = 'PTF'
                        elif band.upper() in ['UVW2', 'UVW1', 'UVM2']:
                            instrument = 'UVOT'
                            telescope = 'Swift'
                            if inpname in ['PTF12dam']:
                                system = 'AB'
                    if inpname in ['SCP-06F6']:
                        system = 'Vega'
                    photodict = {
                        PHOTOMETRY.TIME: mjd,
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.BAND: band,
                        PHOTOMETRY.MAGNITUDE: mag,
                        PHOTOMETRY.UPPER_LIMIT: upperlimit,
                        PHOTOMETRY.SOURCE: source
                    }
                    if instrument:
                        photodict[PHOTOMETRY.INSTRUMENT] = instrument
                    if telescope:
                        photodict[PHOTOMETRY.TELESCOPE] = telescope
                    if survey:
                        photodict[PHOTOMETRY.SURVEY] = survey
                    if system:
                        photodict[PHOTOMETRY.SYSTEM] = system
                    if (is_number(emag) and
                            not isnan(float(emag)) and float(emag) > 0.0):
                        photodict[PHOTOMETRY.E_MAGNITUDE] = emag
                    if isk:
                        photodict[PHOTOMETRY.KCORRECTED] = True
                    catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # Maggi 04-11-16 donation (MC SNRs)
    with open(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Maggi-04-11-16', 'LMCSNRs_OpenSNe.csv')) as f:
        tsvin = csv.reader(f, delimiter=',')
        for row in pbar(list(tsvin), task_str + ': Maggi-04-11-16/LMCSNRs'):
            name = 'MCSNR ' + row[0]
            name = catalog.add_entry(name)
            ra = row[2]
            dec = row[3]
            source = (catalog.entries[name]
                      .add_source(bibcode='2016A&A...585A.162M'))
            catalog.entries[name].add_quantity(
                SUPERNOVA.ALIAS,
                'LMCSNR J' + rep_chars(ra, ' :.') + rep_chars(dec, ' :.'),
                source)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            if row[1] != 'noname':
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1],
                                                   source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[2], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[3], source)
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, 'LMC', source)
            if row[4] == '1':
                catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                   'Ia', source)
            elif row[4] == '2':
                catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                   'CC', source)
    with open(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Maggi-04-11-16', 'SMCSNRs_OpenSNe.csv')) as f:
        tsvin = csv.reader(f, delimiter=',')
        for row in pbar(list(tsvin), task_str + ': Maggi-04-11-16/SMCSNRs'):
            name = 'MCSNR ' + row[0]
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_source(name='Pierre Maggi')
            ra = row[3]
            dec = row[4]
            catalog.entries[name].add_quantity(
                SUPERNOVA.ALIAS, 'SMCSNR J' + ra.replace(
                    ':', '')[:6] + dec.replace(':', '')[:7], source)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[2], source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[3], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[4], source)
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, 'SMC', source)
    catalog.journal_entries()

    # Galbany 04-18-16 donation
    folders = next(
        os.walk(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Galbany-04-18-16/')))[1]
    bibcode = '2016AJ....151...33G'
    for folder in folders:
        infofiles = glob(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Galbany-04-18-16/') + folder + '/*.info')
        photfiles = glob(
            os.path.join(catalog.get_current_task_repo(), 'Donations',
                         'Galbany-04-18-16/') + folder + '/*.out*')

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
                        name += (value[6].upper()
                                 if len(value) == 7 else value[6:])
                        name = catalog.add_entry(name)
                        source = (catalog.entries[name]
                                  .add_source(bibcode=bibcode))
                        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                                           name, source)
                    elif field == 'type':
                        claimedtype = value.replace('SN', '')
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.CLAIMED_TYPE, claimedtype, source)
                    elif field == 'zhel':
                        zhel = value
                    elif field == 'redshift_error':
                        zerr = value
                    elif field == 'zcmb':
                        zcmb = value
                    elif field == 'ra':
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.RA,
                            value,
                            source,
                            u_value='floatdegrees')
                    elif field == 'dec':
                        catalog.entries[name].add_quantity(
                            SUPERNOVA.DEC,
                            value,
                            source,
                            u_value='floatdegrees')
                    elif field == 'host':
                        value = value.replace('- ', '-').replace('G ', 'G')
                        catalog.entries[name].add_quantity(SUPERNOVA.HOST,
                                                           value, source)
                    elif field == 'e(b-v)_mw':
                        catalog.entries[name].add_quantity(SUPERNOVA.EBV,
                                                           value, source)

        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            zhel,
            source,
            e_value=zerr,
            kind='heliocentric')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, zcmb, source, e_value=zerr, kind='cmb')

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
                            time=cols[0],
                            u_time='MJD',
                            magnitude=cols[1],
                            e_magnitude=cols[2],
                            band=band,
                            system=cols[3],
                            telescope=cols[4],
                            source=source)
    catalog.journal_entries()

    # Nicholl 05-03-16
    files = glob(
        os.path.join(catalog.get_current_task_repo(), 'Donations',
                     'Nicholl-05-03-16', '*.txt'))
    name = catalog.add_entry('SN2015bn')
    for fi in pbar(files, task_str + ': Nicholl-05-03-16'):
        if 'late' in fi:
            bc = '2016ApJ...828L..18N'
        else:
            bc = '2016ApJ...826...39N'
        source = catalog.entries[name].add_source(bibcode=bc)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, 'PS15ae', source)
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
                    if not is_number(col) or np.isnan(float(col)):
                        continue

                    band = bands[ci]
                    band_set = ''
                    system = 'Vega'
                    if bands[ci] in ["u'", "g'", "r'", "i'", "z'"]:
                        band_set = 'SDSS'
                        system = 'SDSS'
                    elif telescope == 'ASASSN':
                        band_set = 'ASASSN'
                        system = 'Vega'
                    photodict = {
                        PHOTOMETRY.TIME: mjd,
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.MAGNITUDE: col,
                        PHOTOMETRY.BAND: bands[ci],
                        PHOTOMETRY.SOURCE: source,
                        PHOTOMETRY.TELESCOPE: telescope,
                        PHOTOMETRY.SYSTEM: system
                    }
                    if band_set:
                        photodict[PHOTOMETRY.BAND_SET] = band_set
                    emag = cols[2 * ci + 2]
                    if is_number(emag):
                        photodict[PHOTOMETRY.E_MAGNITUDE] = emag
                    else:
                        photodict[PHOTOMETRY.UPPER_LIMIT] = True
                    if telescope == 'Swift':
                        photodict[PHOTOMETRY.INSTRUMENT] = 'UVOT'
                    catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return


def do_donated_spectra(catalog):
    """Import donated spectra."""
    task_str = catalog.get_current_task_str()
    fpath = os.path.join(catalog.get_current_task_repo(), 'donations')
    with open(os.path.join(fpath, 'meta.json'), 'r') as f:
        metadict = json.loads(f.read())

    donationscnt = 0
    oldname = ''
    for fname in pbar(metadict, task_str):
        name = metadict[fname]['name']
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        sec_bibc = metadict[fname]['bibcode']
        name, source = catalog.new_entry(name, bibcode=sec_bibc)

        date = metadict[fname].get('date', '')
        year, month, day = date.split('/')
        sig = get_sig_digits(day) + 5
        day_fmt = str(floor(float(day))).zfill(2)
        time = astrotime(year + '-' + month + '-' + day_fmt).mjd
        time = time + float(day) - floor(float(day))
        time = pretty_num(time, sig=sig)

        with open(os.path.join(fpath, fname), 'r') as f:
            specdata = list(
                csv.reader(
                    f, delimiter=' ', skipinitialspace=True))
            specdata = list(filter(None, specdata))
            newspec = []
            oldval = ''
            for row in specdata:
                if row[0][0] == '#':
                    continue
                if row[1] == oldval:
                    continue
                newspec.append(row)
                oldval = row[1]
            specdata = newspec
        haserrors = len(specdata[0]) == 3 and specdata[0][2] and specdata[0][
            2] != 'NaN'
        specdata = [list(i) for i in zip(*specdata)]

        wavelengths = specdata[0]
        fluxes = specdata[1]
        errors = ''
        if haserrors:
            errors = specdata[2]

        specdict = {
            SPECTRUM.U_WAVELENGTHS: 'Angstrom',
            SPECTRUM.U_TIME: 'MJD',
            SPECTRUM.TIME: time,
            SPECTRUM.WAVELENGTHS: wavelengths,
            SPECTRUM.FLUXES: fluxes,
            SPECTRUM.ERRORS: errors,
            SPECTRUM.SOURCE: source,
            SPECTRUM.FILENAME: fname
        }
        if 'instrument' in metadict[fname]:
            specdict[SPECTRUM.INSTRUMENT] = metadict[fname]['instrument']
        if 'telescope' in metadict[fname]:
            specdict[SPECTRUM.TELESCOPE] = metadict[fname]['telescope']
        if 'yunit' in metadict[fname]:
            specdict[SPECTRUM.U_FLUXES] = metadict[fname]['yunit']
            specdict[SPECTRUM.U_ERRORS] = metadict[fname]['yunit']
        else:
            if max([float(x) for x in fluxes]) < 1.0e-5:
                fluxunit = 'erg/s/cm^2/Angstrom'
            else:
                fluxunit = 'Uncalibrated'
            specdict[SPECTRUM.U_FLUXES] = fluxunit
            specdict[SPECTRUM.U_ERRORS] = fluxunit
        catalog.entries[name].add_spectrum(**specdict)
        donationscnt = donationscnt + 1
        if (catalog.args.travis and
                donationscnt % catalog.TRAVIS_QUERY_LIMIT == 0):
            break

    catalog.journal_entries()
    return

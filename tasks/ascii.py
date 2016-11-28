# -*- coding: utf-8 -*-
"""ASCII datafiles, often produced from LaTeX tables in the original papers,
but sometimes provided as supplementary datafiles on the journal webpages.
"""
import csv
import os
import re
from datetime import datetime
from glob import glob

from astropy.io.ascii import read
from astropy.time import Time as astrotime

from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.utils import (is_number, jd_to_mjd, make_date_string,
                                     pbar, pbar_strings)
from cdecimal import Decimal

from ..supernova import SUPERNOVA


def do_ascii(catalog):
    """Process ASCII files that were extracted from datatables appearing in
    published works.
    """
    task_str = catalog.get_current_task_str()

    # 2015MNRAS.449.1215P
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2015MNRAS.449.1215P.tsv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0][0] == '#':
            continue
        (name, source) = catalog.new_entry(
            'DES13S2cmm', bibcode='2015MNRAS.449.1215P')
        mjd = row[1]
        for bi, band in enumerate(['g', 'r', 'i', 'z']):
            counts = row[3 + bi].split('±')[0].strip()
            e_counts = row[3 + bi].split('±')[-1].strip()
            if not counts or not e_counts:
                continue
            zp = '31'
            photodict = {
                PHOTOMETRY.TELESCOPE: 'DES',
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.COUNTS: counts,
                PHOTOMETRY.E_COUNTS: e_counts,
                PHOTOMETRY.ZERO_POINT: zp,
                PHOTOMETRY.SOURCE: source
            }
            set_pd_mag_from_counts(photodict, counts, ec=e_counts, zp=zp)
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016MNRAS.459.3939V
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             'Valenti2016_data.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter=' ', skipinitialspace=True))
    bandsub = {
        'BS': 'B',
        'VS': 'V',
        'US': 'U',
        'UM2': 'M2',
        'UW1': 'W1',
        'UW2': 'W2'
    }
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0].startswith('###'):
            continue
        if row[0][0] == '#':
            (name, source) = catalog.new_entry(
                ' '.join(row[1:]).strip().replace('~', ' '),
                bibcode='2016MNRAS.459.3939V')
            continue
        for off in [0, 6]:
            mjd = jd_to_mjd(Decimal(row[1 + off]))
            band = row[4 + off]
            tel = row[5 + off]
            if tel == 'Swift':
                band = band.upper()
                if band in bandsub:
                    band = bandsub[band]
            photodict = {
                PHOTOMETRY.TELESCOPE: tel,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.SOURCE: source
            }
            if tel == 'Swift':
                photodict[PHOTOMETRY.INSTRUMENT] = 'UVOT'
            if row[2 + off] == '<':
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
                photodict[PHOTOMETRY.MAGNITUDE] = row[3 + off]
            else:
                photodict[PHOTOMETRY.MAGNITUDE] = row[2 + off]
                photodict[PHOTOMETRY.E_MAGNITUDE] = row[3 + off]
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2014ApJ...797...24V
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2014ApJ...797...24V-tab1.txt')
    data = read(datafile, format='cds')
    name, source = catalog.new_entry(
        'iPTF13ajg', bibcode='2014ApJ...797...24V')
    for row in pbar(data, task_str):
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: str(row['mag']),
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.SOURCE: source
        }
        if row['l_mag'] == '>':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = str(row['e_mag'])
        catalog.entries[name].add_photometry(**photodict)

    # 2016arXiv160904444J
    bandrep = {
        '[3.6]': 'I1',
        '[4.5]': 'I2',
        '\\text{WB6226-7171}': 'WB6226-7171'
    }

    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2016arXiv160904444J-tab1.tex')

    data = read(datafile, format='latex')
    name, source = catalog.new_entry(
        'SPIRITS 15c', bibcode='2016arXiv160904444J')
    for row in pbar(data, task_str):
        me = [x.replace('$', '') for x in row[5].split('$ $')]
        mag = me[0].replace('>', '').replace('$', '').strip()
        band = row[4].replace('$', '').strip()
        band = bandrep[band] if band in bandrep else band
        tel = row[3].split('/')[0]
        tel = 'Spitzer' if 'Spitzer' in tel else tel
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.TIME: str(row[1]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.TELESCOPE: tel,
            PHOTOMETRY.SOURCE: source
        }
        if '>' in me[0]:
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = me[1].strip().replace(
                '(', '').replace(')', '')
        if len(row[3].split('/')) == 2:
            photodict[PHOTOMETRY.INSTRUMENT] = row[3].split('/')[-1]
        catalog.entries[name].add_photometry(**photodict)

    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2016arXiv160904444J-tab2.tex')

    data = read(datafile, format='latex')
    name, source = catalog.new_entry(
        'SPIRITS 14buu', bibcode='2016arXiv160904444J')
    for row in pbar(data, task_str):
        me = [x.replace('$', '') for x in row[5].split('$ $')]
        mag = me[0].replace('>', '').replace('$', '').strip()
        band = row[4].replace('$', '').strip()
        band = bandrep[band] if band in bandrep else band
        tel = row[3].split('/')[0]
        tel = 'Spitzer' if 'Spitzer' in tel else tel
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.TIME: str(row[1]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.TELESCOPE: tel,
            PHOTOMETRY.SOURCE: source
        }
        if '>' in me[0]:
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = me[1].strip().replace(
                '(', '').replace(')', '')
        if len(row[3].split('/')) == 2:
            photodict[PHOTOMETRY.INSTRUMENT] = row[3].split('/')[-1]
        catalog.entries[name].add_photometry(**photodict)

    # 2011PhDT........35K
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2011PhDT........35K-tab2.2.txt')

    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry('SN2007ax', bibcode='2011PhDT........35K')
    for row in pbar(tsvin[1:], task_str):
        if len(row) == 1:
            continue
        photodict = {
            PHOTOMETRY.MAGNITUDE: row[3],
            PHOTOMETRY.E_MAGNITUDE: row[4],
            PHOTOMETRY.TIME: row[0],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[2],
            PHOTOMETRY.TELESCOPE: row[1],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)

    # 2011ApJ...730..134K
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2011ApJ...730..134K-tab2.txt')

    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry('PTF10fqs', bibcode='2011ApJ...730..134K')
    for row in pbar(tsvin[1:], task_str):
        if len(row) == 1:
            continue
        me = row[2].split(' +or- ')
        mag = me[0].replace('>', '').strip()
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.TIME: str(row[0]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[1].replace('Mould-', ''),
            PHOTOMETRY.TELESCOPE: row[3],
            PHOTOMETRY.SOURCE: source
        }
        if '>' in me[0]:
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = me[1].strip()
        if 'Mould' in row[1]:
            photodict[PHOTOMETRY.BAND_SET] = 'Mould'
        catalog.entries[name].add_photometry(**photodict)

    # 2012ApJ...755..161K
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2012ApJ...755..161K-tab3.txt')

    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    for row in pbar(tsvin[1:], task_str):
        if len(row) == 1:
            name, source = catalog.new_entry(
                row[0], bibcode='2012ApJ...755..161K')
            continue
        me = row[2].split(' +or- ')
        mag = me[0].replace('>', '').strip()
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.TIME: str(row[0]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[1],
            PHOTOMETRY.TELESCOPE: row[3],
            PHOTOMETRY.SOURCE: source
        }
        if '>' in me[0]:
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = me[1].strip()
        catalog.entries[name].add_photometry(**photodict)

    # 2010ApJ...723L..98K
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2010ApJ...723L..98K.tex')

    data = read(datafile, format='latex')
    name, source = catalog.new_entry('SN2010X', bibcode='2010ApJ...723L..98K')
    for row in pbar(data, task_str):
        me = row[2].split(' $\\pm$ ')
        mag = me[0].replace('<', '').replace('$', '').strip()
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.TIME: str(row[0]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[1],
            PHOTOMETRY.TELESCOPE: row[3],
            PHOTOMETRY.SOURCE: source
        }
        if '<' in me[0]:
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = me[1].strip()
        catalog.entries[name].add_photometry(**photodict)

    # 2007ApJ...666.1116S
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2007ApJ...666.1116S-tab1.csv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter=' ', skipinitialspace=True))
    (name, source) = catalog.new_entry(
        'SN2006gy', bibcode='2007ApJ...666.1116S')
    for ri, row in enumerate(pbar(tsvin, task_str)):
        for ci, col in enumerate(row[1:]):
            if col == '-':
                continue
            time, mag, err, upp = row[0], row[1], row[2], row[3]
            photodict = {
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.TELESCOPE: 'KAIT',
                PHOTOMETRY.BAND: 'R',
                PHOTOMETRY.TIME: time,
                PHOTOMETRY.SOURCE: source
            }
            if upp == '1':
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2015ApJ...799...51M
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2015ApJ...799...51M-tab1.tsv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
    (name, source) = catalog.new_entry(
        'SN2012ap', bibcode='2015ApJ...799...51M')
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0][0] == '#':
            bands = row[1:]
            continue
        for ci, col in enumerate(row[1:]):
            if col == '-':
                continue
            mag, err = col.split()[0], col.split()[1]
            photodict = {
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.TELESCOPE: 'KAIT',
                PHOTOMETRY.BAND: bands[ci],
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2013ApJ...767...57F
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2013ApJ...767...57F.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter=' ', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        (name, source) = catalog.new_entry(
            row[0], bibcode='2013ApJ...767...57F')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'Ia-02cx',
                                           source)

    # 2015MNRAS.446.3895F
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2015MNRAS.446.3895F.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter=' ', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0][0] == '#':
            continue
        (name, source) = catalog.new_entry(
            row[0], bibcode='2015MNRAS.446.3895F')
        counts = row[3].rstrip('0')
        e_counts = row[4].rstrip('0')
        if row[1].startswith('LSQ'):
            off = 2
        else:
            off = 1
        zp = row[5].rstrip('0')
        photodict = {
            PHOTOMETRY.INSTRUMENT: row[1][:-off],
            PHOTOMETRY.BAND: row[1][-off:],
            PHOTOMETRY.TIME: row[2],
            PHOTOMETRY.COUNTS: counts,
            PHOTOMETRY.E_COUNTS: e_counts,
            PHOTOMETRY.ZERO_POINT: zp,
            PHOTOMETRY.SOURCE: source
        }
        set_pd_mag_from_counts(photodict, counts, ec=e_counts, zp=zp)
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2015arXiv150907124M
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2015arXiv150907124M.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='/', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0][0] == '#':
            ct = row[0].lstrip('#')
            continue
        name = row[0]
        (name, source) = catalog.new_entry(name, bibcode='2015arXiv150907124M')
        if len(row) == 2:
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, ct, source)
    catalog.journal_entries()

    # 2003ApJ...599..394M
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2003ApJ...599..394M-tab1.txt')
    data = read(datafile, format='cds')
    name, source = catalog.new_entry('SN2003dh', bibcode='2003ApJ...599..394M')
    for row in pbar(data, task_str):
        photodict = {
            PHOTOMETRY.TIME:
            str(Decimal(str(row['DelT'])) + Decimal("52727.4842")),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: str(row['mag']),
            PHOTOMETRY.E_MAGNITUDE: str(row['e_mag']),
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.OBSERVATORY: row['Obs'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)

    # 2004ApJ...606..381L
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2004ApJ...606..381L-table3.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter=' ', skipinitialspace=True))
    name = 'SN2003dh'
    (name, source) = catalog.new_entry(name, bibcode='2004ApJ...606..381L')
    instdict = {}
    banddict = {}
    bibdict = {}
    bibs = {
        'Uemura': '2003Natur.423..843U',
        'Burenin': '2003AstL...29..573B',
        'Bloom': '2004AJ....127..252B',
        'Matheson': '2003ApJ...599..394M'
    }
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if not row:
            continue
        if ri >= 23 and ri <= 38:
            instbibstr = (' '.join(row[2:])).rstrip('.;')
            instdict[row[0]] = instbibstr.split('(')[0].strip()
            bc = ''
            for bib in bibs:
                if bib in instbibstr:
                    bc = bibs[bib]
            bibdict[row[0]] = bc
        elif ri >= 40 and ri <= 43:
            banddict[row[0]] = row[2]
        elif ri >= 45:
            time = str(jd_to_mjd(Decimal(row[2]) + Decimal('2450000')))
            ssource = ''
            if bibdict[row[0]]:
                # Skip Matheson as it's added directly above
                if bibdict[row[0]] == '2003ApJ...599..394M':
                    continue
                ssource = catalog.entries[name].add_source(
                    bibcode=bibdict[row[0]])
            photodict = {
                'instrument': instdict[row[0]],
                'band': banddict[row[1]],
                'time': time,
                'magnitude': row[4],
                'e_magnitude': row[6],
                'source': source + ((',' + ssource) if ssource else '')
            }
            catalog.entries[name].add_photometry(**photodict)
        else:
            continue
    catalog.journal_entries()

    # 2006ApJ...645..841N
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2006ApJ...645..841N-table3.csv')
    tsvin = list(csv.reader(open(file_path, 'r'), delimiter=','))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        name = 'SNLS-' + row[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2006ApJ...645..841N')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row[1], source, kind='spectroscopic')
        astrot = astrotime(float(row[4]) + 2450000., format='jd').datetime
        date_str = make_date_string(astrot.year, astrot.month, astrot.day)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, date_str,
                                           source)
    catalog.journal_entries()

    # Anderson 2014
    file_names = list(
        glob(
            os.path.join(catalog.get_current_task_repo(),
                         'SNII_anderson2014/*.dat')))
    for datafile in pbar_strings(file_names, task_str):
        basename = os.path.basename(datafile)
        if not is_number(basename[:2]):
            continue
        if basename == '0210_V.dat':
            name = 'SN0210'
        else:
            name = ('SN20' if int(basename[:2]) < 50 else 'SN19'
                    ) + basename.split('_')[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...786...67A')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

        if name in ['SN1999ca', 'SN2003dq', 'SN2008aw']:
            band_set = 'Swope'
            system = 'Swope'
        else:
            band_set = 'Johnson-Cousins'
            system = 'Landolt'

        with open(datafile, 'r') as ff:
            tsvin = csv.reader(ff, delimiter=' ', skipinitialspace=True)
            for row in tsvin:
                if not row[0]:
                    continue
                time = str(jd_to_mjd(Decimal(row[0])))
                catalog.entries[name].add_photometry(
                    time=time,
                    u_time='MJD',
                    band='V',
                    magnitude=row[1],
                    e_magnitude=row[2],
                    bandset=band_set,
                    system=system,
                    source=source)
    catalog.journal_entries()

    # stromlo
    stromlobands = ['B', 'V', 'R', 'I', 'VM', 'RM']
    file_path = os.path.join(catalog.get_current_task_repo(),
                             'J_A+A_415_863-1/photometry.csv')
    tsvin = list(csv.reader(open(file_path, 'r'), delimiter=','))
    for row in pbar(tsvin, task_str):
        name = row[0]
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2004A&A...415..863G')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        mjd = str(jd_to_mjd(Decimal(row[1])))
        for ri, ci in enumerate(range(2, len(row), 3)):
            if not row[ci]:
                continue
            band = stromlobands[ri]
            upperlimit = True if (not row[ci + 1] and row[ci + 2]) else False
            e_upper_magnitude = str(abs(Decimal(row[ci + 1]))) if row[
                ci + 1] else ''
            e_lower_magnitude = str(abs(Decimal(row[ci + 2]))) if row[
                ci + 2] else ''
            teles = 'MSSSO 1.3m' if band in ['VM', 'RM'] else 'CTIO'
            instr = 'MaCHO' if band in ['VM', 'RM'] else ''
            catalog.entries[name].add_photometry(
                time=mjd,
                u_time='MJD',
                band=band,
                magnitude=row[ci],
                e_upper_magnitude=e_upper_magnitude,
                e_lower_magnitude=e_lower_magnitude,
                upperlimit=upperlimit,
                telescope=teles,
                instrument=instr,
                source=source)
    catalog.journal_entries()

    # 2015MNRAS.449..451W
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2015MNRAS.449..451W.dat')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    for rr, row in enumerate(pbar(data, task_str)):
        if rr == 0:
            continue
        namesplit = row[0].split('/')
        name = namesplit[-1]
        if name.startswith('SN'):
            name = name.replace(' ', '')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.449..451W')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if len(namesplit) > 1:
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, namesplit[0],
                                               source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row[1],
                                           source)
        catalog.entries[name].add_photometry(
            time=row[2],
            u_time='MJD',
            band=row[4],
            magnitude=row[3],
            source=source)
    catalog.journal_entries()

    # 2016MNRAS.459.1039T
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2016MNRAS.459.1039T.tsv')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    name = catalog.add_entry('LSQ13zm')
    source = catalog.entries[name].add_source(bibcode='2016MNRAS.459.1039T')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for rr, row in enumerate(pbar(data, task_str)):
        if row[0][0] == '#':
            bands = [xx.replace('(err)', '') for xx in row[3:-1]]
            continue
        mjd = row[1]
        mags = [re.sub(r'\([^)]*\)', '', xx) for xx in row[3:-1]]
        upps = [True if '>' in xx else '' for xx in mags]
        mags = [xx.replace('>', '') for xx in mags]
        errs = [
            xx[xx.find('(') + 1:xx.find(')')] if '(' in xx else ''
            for xx in row[3:-1]
        ]
        for mi, mag in enumerate(mags):
            if not is_number(mag):
                continue
            catalog.entries[name].add_photometry(
                time=mjd,
                u_time='MJD',
                band=bands[mi],
                magnitude=mag,
                e_magnitude=errs[mi],
                instrument=row[-1],
                upperlimit=upps[mi],
                source=source)
    catalog.journal_entries()

    # 2015ApJ...804...28G
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2015ApJ...804...28G.tsv')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    name = catalog.add_entry('PS1-13arp')
    source = catalog.entries[name].add_source(bibcode='2015ApJ...804...28G')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for rr, row in enumerate(pbar(data, task_str)):
        if rr == 0:
            continue
        mjd = row[1]
        mag = row[3]
        upp = True if '<' in mag else ''
        mag = mag.replace('<', '')
        err = row[4] if is_number(row[4]) else ''
        ins = row[5]
        catalog.entries[name].add_photometry(
            time=mjd,
            u_time='MJD',
            band=row[0],
            magnitude=mag,
            e_magnitude=err,
            instrument=ins,
            upperlimit=upp,
            source=source)
    catalog.journal_entries()

    # 2016ApJ...819...35A
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2016ApJ...819...35A.tsv')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    for rr, row in enumerate(pbar(data, task_str)):
        if row[0][0] == '#':
            continue
        name = catalog.add_entry(row[0])
        source = catalog.entries[name].add_source(
            bibcode='2016ApJ...819...35A')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
        catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[3], source)
        disc_date = datetime.strptime(row[4], '%Y %b %d').isoformat()
        disc_date = disc_date.split('T')[0].replace('-', '/')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, disc_date,
                                           source)
    catalog.journal_entries()

    # 2014ApJ...784..105W
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2014ApJ...784..105W.tsv')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    for rr, row in enumerate(pbar(data, task_str)):
        if row[0][0] == '#':
            continue
        name = catalog.add_entry(row[0])
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...784..105W')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        mjd = row[1]
        band = row[2]
        mag = row[3]
        err = row[4]
        catalog.entries[name].add_photometry(
            time=mjd,
            u_time='MJD',
            band=row[2],
            magnitude=mag,
            e_magnitude=err,
            instrument='WHIRC',
            telescope='WIYN 3.5 m',
            observatory='NOAO',
            bandset='Johnson-Cousins',
            system='WHIRC',
            source=source)
    catalog.journal_entries()

    # 2012MNRAS.425.1007B
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2012MNRAS.425.1007B.tsv')
    data = list(
        csv.reader(
            open(file_path, 'r'),
            delimiter='\t',
            quotechar='"',
            skipinitialspace=True))
    for rr, row in enumerate(pbar(data, task_str)):
        if row[0][0] == '#':
            bands = row[2:]
            continue
        name = catalog.add_entry(row[0])
        source = catalog.entries[name].add_source(
            bibcode='2012MNRAS.425.1007B')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        mjd = row[1]
        mags = [xx.split('±')[0].strip() for xx in row[2:]]
        errs = [
            xx.split('±')[1].strip() if '±' in xx else '' for xx in row[2:]
        ]
        if row[0] == 'PTF09dlc':
            ins = 'HAWK-I'
            tel = 'VLT 8.1m'
            obs = 'ESO'
        else:
            ins = 'NIRI'
            tel = 'Gemini North 8.2m'
            obs = 'Gemini'

        for mi, mag in enumerate(mags):
            if not is_number(mag):
                continue
            catalog.entries[name].add_photometry(
                time=mjd,
                u_time='MJD',
                band=bands[mi],
                magnitude=mag,
                e_magnitude=errs[mi],
                instrument=ins,
                telescope=tel,
                observatory=obs,
                system='Natural',
                source=source)

        catalog.journal_entries()

    # 2014ApJ...783...28G
    file_path = os.path.join(catalog.get_current_task_repo(),
                             'apj490105t2_ascii.txt')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            name, source = catalog.new_entry(
                row[0], bibcode='2014ApJ...783...28G')
            spz = is_number(row[13])
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                               '20' + row[0][3:5], source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[2], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[3], source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                row[13] if spz else row[10],
                source,
                kind=('spectroscopic' if spz else 'photometric'))
    catalog.journal_entries()

    # 2005ApJ...634.1190H
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2005ApJ...634.1190H.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            name, source = catalog.new_entry(
                'SNLS-' + row[0], bibcode='2005ApJ...634.1190H')
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                               '20' + row[0][:2], source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                row[5].replace('?', ''),
                source,
                e_value=row[6],
                kind='host')
            catalog.entries[name].add_quantity(
                SUPERNOVA.CLAIMED_TYPE, row[7].replace('SN', '').strip(':* '),
                source)
    catalog.journal_entries()

    # 2014MNRAS.444.2133S
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2014MNRAS.444.2133S.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                continue
            name = row[0]
            if is_number(name[:4]):
                name = 'SN' + name
            name, source = catalog.new_entry(
                name, bibcode='2014MNRAS.444.2133S')
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, row[3], source, kind='host')
    catalog.journal_entries()

    # 2009MNRAS.398.1041B
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2009MNRAS.398.1041B.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                bands = row[2:-1]
                continue
            name, source = catalog.new_entry(
                'SN2008S', bibcode='2009MNRAS.398.1041B')
            mjd = str(jd_to_mjd(Decimal(row[0])))
            mags = [x.split('±')[0].strip() for x in row[2:]]
            upps = [('<' in x.split('±')[0]) for x in row[2:]]
            errs = [
                x.split('±')[1].strip() if '±' in x else '' for x in row[2:]
            ]

            instrument = row[-1]

            for mi, mag in enumerate(mags):
                if not is_number(mag):
                    continue
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    band=bands[mi],
                    magnitude=mag,
                    e_magnitude=errs[mi],
                    instrument=instrument,
                    source=source)
    catalog.journal_entries()

    # 2010arXiv1007.0011P
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2010arXiv1007.0011P.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                bands = row[1:]
                continue
            name, source = catalog.new_entry(
                'SN2008S', bibcode='2010arXiv1007.0011P')
            mjd = row[0]
            mags = [x.split('±')[0].strip() for x in row[1:]]
            errs = [
                x.split('±')[1].strip() if '±' in x else '' for x in row[1:]
            ]

            for mi, mag in enumerate(mags):
                if not is_number(mag):
                    continue
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    band=bands[mi],
                    magnitude=mag,
                    e_magnitude=errs[mi],
                    instrument='LBT',
                    source=source)
    catalog.journal_entries()

    # 2000ApJ...533..320G
    file_path = os.path.join(catalog.get_current_task_repo(),
                             '2000ApJ...533..320G.tsv')
    with open(file_path, 'r') as f:
        data = list(
            csv.reader(
                f, delimiter='\t', quotechar='"', skipinitialspace=True))
        name, source = catalog.new_entry(
            'SN1997cy', bibcode='2000ApJ...533..320G')
        for r, row in enumerate(pbar(data, task_str)):
            if row[0][0] == '#':
                bands = row[1:-1]
                continue
            mjd = str(jd_to_mjd(Decimal(row[0])))
            mags = row[1:len(bands)]
            for mi, mag in enumerate(mags):
                if not is_number(mag):
                    continue
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    band=bands[mi],
                    magnitude=mag,
                    observatory='Mount Stromlo',
                    telescope='MSSSO',
                    source=source,
                    kcorrected=True)

    catalog.journal_entries()
    return

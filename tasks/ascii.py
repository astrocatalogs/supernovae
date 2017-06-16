# -*- coding: utf-8 -*-
"""ASCII datafiles.

Often produced from LaTeX tables in the original papers,
but sometimes provided as supplementary datafiles on the journal webpages.
"""
import csv
import os
import re
from datetime import datetime
from decimal import Decimal
from glob import glob

from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.utils import (is_number, jd_to_mjd, make_date_string,
                                     pbar, pbar_strings)
from astropy import units as u
from astropy.coordinates import SkyCoord as coord
from astropy.io.ascii import read
from astropy.time import Time as astrotime

from ..supernova import SUPERNOVA


def do_ascii(catalog):
    """Process ASCII files extracted from datatables of published works."""
    task_str = catalog.get_current_task_str()

    # 2017ApJ...836...60L
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2017ApJ...836...60L-tab1.cds')
    data = read(datafile, format='cds')
    for row in pbar(data, task_str):
        oname = row['ID']
        name, source = catalog.new_entry(oname, bibcode='2017ApJ...836...60L')
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2017arXiv170601030H
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            'CFA_SNII_NATSYSTEM_LC.txt')
    data = read(datafile, format='tab')
    for row in pbar(data, task_str):
        oname = row[0]
        name, source = catalog.new_entry(oname, bibcode='2017arXiv170601030H')
        photodict = {
            PHOTOMETRY.TIME: row[2],
            PHOTOMETRY.MAGNITUDE: row[4],
            PHOTOMETRY.E_MAGNITUDE: row[5],
            PHOTOMETRY.BAND: row[1],
            PHOTOMETRY.INSTRUMENT: row[7],
            PHOTOMETRY.SURVEY: row[6],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            'CFA_SNII_NIR_LC.txt')
    data = read(datafile, format='tab')
    for row in pbar(data, task_str):
        oname = row[0]
        name, source = catalog.new_entry(oname, bibcode='2017arXiv170601030H')
        photodict = {
            PHOTOMETRY.TIME: row[2],
            PHOTOMETRY.MAGNITUDE: row[3],
            PHOTOMETRY.E_MAGNITUDE: row[4],
            PHOTOMETRY.BAND: row[1],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 1705.10806
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '1705.10806.tex')
    data = read(datafile, format='latex')
    for row in pbar(data, task_str):
        oname = row['Supernova']
        name, source = catalog.new_entry(oname, arxivid='1705.10806')
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.MAGNITUDE: row['Magnitude'],
            PHOTOMETRY.E_MAGNITUDE: row['Error'],
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.TELESCOPE: row['Telescope'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 1705.10927
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '1705.10927.tex')
    data = read(datafile, format='latex')
    for row in pbar(data, task_str):
        oname = row[0].replace('$', '')
        name, source = catalog.new_entry(oname, arxivid='1705.10927')
        catalog.entries[name].add_quantity(
            SUPERNOVA.ALIAS, 'MWSNR' + oname[1:], source=source)
        gallon = float(str(row[1]).replace('$', ''))
        gallat = float(str(row[2]).replace('$', ''))
        ra, dec = coord(
            l=gallon * u.degree, b=gallat * u.degree,
            frame='galactic').icrs.to_string(
                'hmsdms', sep=':').split()
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST, 'Milky Way', source=source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, ra, source=source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, dec, source=source)
    catalog.journal_entries()

    # 2000MNRAS.319..223H
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2000MNRAS.319..223H.csv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter=',', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN1998bu', bibcode='2000MNRAS.319..223H')
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if ri == 0:
            continue
        mjd = jd_to_mjd(Decimal('2450000') + Decimal(row[0]))
        for bi, band in enumerate(['J', 'H', 'K']):
            photodict = {
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: row[2 * bi + 1],
                PHOTOMETRY.E_MAGNITUDE: row[2 * bi + 2],
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.TELESCOPE: row[-2],
                PHOTOMETRY.OBSERVER: row[-1],
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2017arXiv170405061Y
    events = {
        'iPTF15esb': '1704.05061-tab3.tsv',
        'iPTF16bad': '1704.05061-tab4.tsv'
    }
    for ev in events:
        datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                                events[ev])
        tsvin = list(
            csv.reader(
                open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
        name, source = catalog.new_entry(
            ev, bibcode='2017arXiv170405061Y')
        for row in pbar(tsvin, task_str):
            photodict = {
                PHOTOMETRY.TIME: row[1],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: row[2],
                PHOTOMETRY.E_MAGNITUDE: row[3],
                PHOTOMETRY.BAND: row[0],
                PHOTOMETRY.SYSTEM: 'AB',
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...823..147C
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2016ApJ...823..147C.csv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter=',', skipinitialspace=True))
    name, src1 = catalog.new_entry(
        'iPTF13asv', bibcode='2016ApJ...823..147C')
    src2 = catalog.entries[name].add_source(bibcode='2012PASP..124..668Y')
    source = ','.join([src1, src2])
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            continue
        mag = row[1]
        err = row[2]
        photodict = {
            PHOTOMETRY.TIME: row[0],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.BAND: row[-2],
            PHOTOMETRY.TELESCOPE: row[-1],
            PHOTOMETRY.SOURCE: source
        }
        if err == '99':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = err
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2014MNRAS.443.1663C
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2014MNRAS.443.1663C.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN2012dn', bibcode='2014MNRAS.443.1663C')
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            bands = row[1:]
            continue
        for bi, band in enumerate(bands):
            if row[bi + 1].strip() == '-':
                continue
            mag, err = tuple([x.strip() for x in row[bi + 1].split('±')])
            photodict = {
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[0])),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2015ApJ...811...52A
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2015ApJ...811...52A.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'PTF12csy', bibcode='2015ApJ...811...52A')
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            continue
        mag = row[1]
        if mag == '-':
            continue
        mag, err = tuple([x.strip() for x in mag.split('±')])
        photodict = {
            PHOTOMETRY.TIME: row[0],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.E_MAGNITUDE: err,
            PHOTOMETRY.BAND: row[-2],
            PHOTOMETRY.TELESCOPE: row[-1],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)

    # 2015MNRAS.450.2373B
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2015MNRAS.450.2373B.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN2013ab', bibcode='2015MNRAS.450.2373B')
    telkey = {
        '1': 'ST/DFOT',
        '2': 'Faulkes Telescope South',
        '3': 'Faulkes Telescope North',
        '5': '1-m LCOGT',
        '6': 'IAUC'
    }
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            bands = row[1:]
            continue
        for bi, band in enumerate(bands):
            if row[bi + 1].strip() == '–':
                continue
            photodict = {
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[0])),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.TELESCOPE: '/'.join(
                    [telkey[x] for x in row[-1].strip().split(',')]),
                PHOTOMETRY.SOURCE: source
            }
            if '>' in row[bi + 1]:
                mag = row[bi + 1].strip('>')
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            else:
                magerr = tuple([x.strip() for x in row[bi + 1].split('±')])
                if len(magerr) == 2:
                    mag, err = magerr
                    photodict[PHOTOMETRY.E_MAGNITUDE] = err
                else:
                    mag = magerr[0]
            photodict[PHOTOMETRY.MAGNITUDE] = mag
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2014ApJ...797....5Z
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2014ApJ...797....5Z.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN2013am', bibcode='2014ApJ...797....5Z')
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            bands = row[1:]
            continue
        telescope = row[-1]
        for bi, band in enumerate(bands):
            if row[bi + 1].strip() == '-':
                continue
            mag, err = tuple([x.strip() for x in row[bi + 1].split('(')])
            err = str(Decimal('0.01') * Decimal(err.strip(')')))
            photodict = {
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.TELESCOPE: telescope,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2015MNRAS.452..838L
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2015MNRAS.452..838L.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN2013en', bibcode='2015MNRAS.452..838L')
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            bands = row[1:]
            continue
        telescope, instrument = tuple(row[-2].split('+'))
        observer = row[-1]
        for bi, band in enumerate(bands):
            if row[bi + 1].strip() == '–':
                continue
            mag, err = tuple([x.strip() for x in row[bi + 1].split('(')])
            err = str(Decimal('0.01') * Decimal(err.strip(')')))
            photodict = {
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.INSTRUMENT: instrument,
                PHOTOMETRY.TELESCOPE: telescope,
                PHOTOMETRY.OBSERVER: observer,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2015MNRAS.452.4307P
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2015MNRAS.452.4307P.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry(
        'SN2013dy', bibcode='2015MNRAS.452.4307P')
    for row in pbar(tsvin, task_str):
        if row[0].startswith('#'):
            instrument = row[0].strip('#')
            bands = row[1:]
            continue
        for bi, band in enumerate(bands):
            if row[bi + 1].strip() == '–':
                continue
            mag, err = tuple([x.strip() for x in row[bi + 1].split('±')])
            photodict = {
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.E_MAGNITUDE: err,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.INSTRUMENT: instrument,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016MNRAS.461.2003Y
    path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                        '2016MNRAS.461.2003Y-tab2.txt')
    tsvin = list(
        csv.reader(
            open(path, 'r'), delimiter=',', skipinitialspace=True))
    name, source = catalog.new_entry('SN2013ej',
                                     bibcode='2016MNRAS.461.2003Y')
    telstring = ','.join(tsvin[-1]).strip('#')
    tels = {}
    for combo in telstring.split(';'):
        combosplit = combo.split(':')
        keys = [x.strip() for x in combosplit[0].split(',')]
        value = combosplit[1].strip()
        for key in keys:
            tels[key] = value

    for row in pbar(tsvin, desc=task_str):
        if not row or row[0][0] == '#':
            continue
        mag, err = tuple([x.strip('() ') for x in row[2].split()])
        photodict = {
            PHOTOMETRY.TIME: row[1].strip(),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.E_MAGNITUDE: err,
            PHOTOMETRY.BAND: row[3].strip(),
            PHOTOMETRY.TELESCOPE: tels[row[-1].strip()],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2017arXiv170302402W
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'SweetSpot', '*.dat'))
    for path in pbar(file_names, desc=task_str + ', SweetSpot'):
        tsvin = list(
            csv.reader(
                open(path, 'r'), delimiter=' ', skipinitialspace=True))
        oname = path.split('/')[-1].split('_')[0]
        name, source = catalog.new_entry(oname, bibcode='2017arXiv170302402W')
        for row in tsvin:
            if not row or row[0][0] == '#':
                continue
            inst, band = row[2][:-1], row[2][-1]
            tel = 'WIYN'
            zp = '25'
            c, lec, uec = tuple(row[3:6])
            photodict = {
                PHOTOMETRY.TIME: row[1],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.COUNT_RATE: c,
                PHOTOMETRY.E_LOWER_COUNT_RATE: lec,
                PHOTOMETRY.E_UPPER_COUNT_RATE: uec,
                PHOTOMETRY.BAND: band,
                PHOTOMETRY.INSTRUMENT: inst,
                PHOTOMETRY.TELESCOPE: tel,
                PHOTOMETRY.SOURCE: source
            }
            set_pd_mag_from_counts(photodict, c, lec=lec, uec=uec, zp=zp)
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2014ApJ...789..104O
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2014ApJ...789..104O-tab1.txt')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    for row in pbar(tsvin[2:], task_str):
        name, source = catalog.new_entry(row[0], bibcode='2014ApJ...789..104O')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row[1],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row[2], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row[3], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[5], source)
    catalog.journal_entries()

    zps = {
        'default': '27',
        'PTF10aazn': '27.895',
        'PTF10bjb': '27.14',
        'PTF10tel': '27.442'
    }
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2014ApJ...789..104O-tab2.txt')
    data = read(datafile, format='cds')
    for row in pbar(data, task_str):
        oname = row['SN']
        name, source = catalog.new_entry(oname, bibcode='2014ApJ...789..104O')
        c = str(row['Flux'])
        ec = str(row['e_Flux'])
        zp = zps[oname] if oname in zps else zps['default']
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.COUNT_RATE: c,
            PHOTOMETRY.E_COUNT_RATE: ec,
            PHOTOMETRY.SOURCE: source
        }
        set_pd_mag_from_counts(photodict, c, ec=ec, zp=zp)
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # KEGS
    # Zero point not right, commenting out for now.
    # file_names = list(
    #     glob(os.path.join(catalog.get_current_task_repo(), 'KEGS', '*.dat')))
    # for path in pbar(file_names, task_str):
    #     oname = path.split('/')[-1].split('.')[0]
    #     name, source = catalog.new_entry(
    #         oname, srcname='KEGS', url='http://www.mso.anu.edu.au/kegs/')
    #     tsvin = list(
    #         csv.reader(
    #             open(path, 'r'), delimiter=' ', skipinitialspace=True))
    #     for row in pbar(tsvin, oname):
    #         if row[0][0] == '#':
    #             continue
    #         counts = row[3]
    #         e_counts = row[4]
    #         zp = '25.47'
    #         photodict = {
    #             PHOTOMETRY.TIME:
    #             jd_to_mjd(Decimal(row[0]) + Decimal('2454833')),
    #             PHOTOMETRY.BAND: 'Kepler',
    #             PHOTOMETRY.U_TIME: 'MJD',
    #             PHOTOMETRY.COUNT_RATE: counts,
    #             PHOTOMETRY.E_COUNT_RATE: e_counts,
    #             PHOTOMETRY.ZERO_POINT: zp,
    #             PHOTOMETRY.SOURCE: source
    #         }
    #         set_pd_mag_from_counts(photodict, counts, ec=e_counts, zp=zp)
    #         catalog.entries[name].add_photometry(**photodict)

    # Howerton Catalog
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            'howerton-catalog.csv')
    data = read(datafile, format='csv')
    for rrow in pbar(data, task_str):
        row = dict((x, str(rrow[x])) for x in rrow.columns)
        if any(x in row['Notes'].lower() for x in ['artifact']):
            continue
        ctypes = row['Type'].split('/')
        nonsne = False
        for ct in ctypes:
            if ct.replace('?', '') in catalog.nonsnetypes:
                nonsne = True
            else:
                nonsne = False
                break
        if nonsne:
            continue
        name, source = catalog.new_entry(
            row['SNHunt des.'],
            srcname='CRTS SNhunt',
            bibcode='2017csnh.book.....H')
        if row['IAU des.'] != '--':
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                               row['IAU des.'], source)
        for ct in ctypes:
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, ct,
                                               source)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER,
                                           row['Discoverer'], source)
        date = row['Discovery'].split('/')
        date = '/'.join([date[-1].zfill(2), date[0].zfill(2), date[1]])
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, date,
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST, row['Host galaxy'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RA'].replace(
            'h', ':').replace('m', ':').replace('s', ''), source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['Dec'], source)
    catalog.journal_entries()

    # 2006AJ....132.2024L
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2006AJ....132.2024L-tab1.txt')
    data = read(datafile, format='cds')
    for row in pbar(data, task_str):
        name, source = catalog.new_entry(
            row['Name'], bibcode='2006AJ....132.2024L')
        for band in [
                x for x in row.columns
                if x.endswith('mag') and not x.startswith('e_')
        ]:
            if not is_number(row[band]):
                continue
            photodict = {
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(str(row['JD']))),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: str(row[band]),
                PHOTOMETRY.BAND: band.replace('mag', ''),
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2006AJ....132.1126N
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2006AJ....132.1126N-tab2.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    for row in pbar(tsvin, task_str):
        name, source = catalog.new_entry(row[0], bibcode='2006AJ....132.1126N')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row[3], source, kind='spectroscopic')
        mldt = astrotime(float(row[4]), format='mjd').datetime
        discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           discoverdate, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, kind='spectroscopic')

    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2006AJ....132.1126N-tab3.tsv')
    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    for row in pbar(tsvin, task_str):
        name, source = catalog.new_entry(row[0], bibcode='2006AJ....132.1126N')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[1], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[2], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row[3], source, kind='photometric')
        mldt = astrotime(float(row[4]), format='mjd').datetime
        discoverdate = make_date_string(mldt.year, mldt.month, mldt.day)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           discoverdate, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia?', source, kind='photometric')
    catalog.journal_entries()

    # 2007ApJ...669L..17H
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2007ApJ...669L..17H.tsv')

    tsvin = list(
        csv.reader(
            open(datafile, 'r'), delimiter='\t', skipinitialspace=True))
    name, source = catalog.new_entry('SN2006gz', bibcode='2007ApJ...669L..17H')
    for row in pbar(tsvin[1:], task_str):
        photodict = {
            PHOTOMETRY.MAGNITUDE: row[2],
            PHOTOMETRY.E_MAGNITUDE: row[3],
            PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[1])),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row[0],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2011ApJ...729...88R
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2011ApJ...729...88R-tab1.tsv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        (name, source) = catalog.new_entry(
            'SN2003ma', bibcode='2011ApJ...729...88R')
        if ri == 0:
            bands = row[1:]
            continue
        for ci, col in enumerate(row[1:]):
            csplit = col.split(' (')
            if not is_number(csplit[0]):
                continue
            photodict = {
                PHOTOMETRY.BAND: bands[ci].split('_')[0],
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.MAGNITUDE: csplit[0].strip('<'),
                PHOTOMETRY.SURVEY: ('SuperMONGO'
                                    if '_SM' in bands[ci] else 'OGLE'),
                PHOTOMETRY.SOURCE: source
            }
            if len(csplit) > 1:
                err = csplit[1].strip(')')
                photodict[PHOTOMETRY.E_MAGNITUDE] = err
            if '<' in col:
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 1998A&A...337..207S
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '1998A&A...337..207S-tab3.tsv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        (name, source) = catalog.new_entry(
            'SN1996N', bibcode='1998A&A...337..207S')
        if ri == 0:
            bands = row[1:]
            continue
        for ci, col in enumerate(row[1:-1:2]):
            if not is_number(col):
                continue
            photodict = {
                PHOTOMETRY.BAND: bands[ci],
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[0])),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: col,
                PHOTOMETRY.SOURCE: source
            }
            if is_number(row[2 + 2 * ci]):
                photodict[PHOTOMETRY.E_MAGNITUDE] = row[2 + 2 * ci]
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 1997ApJ...483..675C
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '1997ApJ...483..675C-tab1.tsv')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        (name, source) = catalog.new_entry(
            'SN1983V', bibcode='1997ApJ...483..675C')
        if ri == 0:
            bands = row[1:-2]
            continue
        for ci, col in enumerate(row[1:-2:2]):
            if not is_number(col):
                continue
            photodict = {
                PHOTOMETRY.TELESCOPE: row[-2],
                PHOTOMETRY.BAND: bands[ci],
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[0])),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: col,
                PHOTOMETRY.SOURCE: source
            }
            if is_number(row[2 + 2 * ci]):
                photodict[PHOTOMETRY.E_MAGNITUDE] = row[2 + 2 * ci]
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2017ApJ...835...58V
    datafile = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                            '2017ApJ...835...58V-tab11.tex')

    data = read(datafile, format='latex')
    name, source = catalog.new_entry(
        'iPTF13dcc', bibcode='2017ApJ...835...58V')
    for row in pbar(data, task_str):
        mag, err = row[-1].split(' $\pm$ ')
        band = row[3]
        tel = row[2]
        photodict = {
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.E_MAGNITUDE: err,
            PHOTOMETRY.TIME: str(row[0]),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.TELESCOPE: tel,
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2012A&A...537A.140T
    tables = ['2012A&A...537A.140T-' + x + '.tsv' for x in ['tab4', 'tab6']]
    sns = ['SN2006V', 'SN2006au']
    for ti, tab in enumerate(tables):
        file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII', tab)
        tsvin = list(
            csv.reader(
                open(file_path, 'r'), delimiter='\t', skipinitialspace=True))
        for ri, row in enumerate(pbar(tsvin, task_str)):
            (name, source) = catalog.new_entry(
                sns[ti], bibcode='2012A&A...537A.140T')
            if ri == 0:
                bands = row[1:]
                continue
            for ci, col in enumerate(row[1:-1:2]):
                if not is_number(col):
                    continue
                photodict = {
                    PHOTOMETRY.TELESCOPE: row[-1],
                    PHOTOMETRY.BAND: bands[ci],
                    PHOTOMETRY.TIME: jd_to_mjd(Decimal(row[0])),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.MAGNITUDE: col,
                    PHOTOMETRY.E_MAGNITUDE: str(float(row[2 + 2 * ci])),
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

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
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.COUNT_RATE: counts,
                PHOTOMETRY.E_COUNT_RATE: e_counts,
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
        if row['MJD'] >= 56600:
            photodict[PHOTOMETRY.HOST] = True
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
            PHOTOMETRY.COUNT_RATE: counts,
            PHOTOMETRY.E_COUNT_RATE: e_counts,
            PHOTOMETRY.ZERO_POINT: zp,
            PHOTOMETRY.SOURCE: source
        }
        set_pd_mag_from_counts(photodict, counts, ec=e_counts, zp=zp)
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...832..108M
    file_path = os.path.join(catalog.get_current_task_repo(), 'ASCII',
                             '2016ApJ...832..108M.txt')
    tsvin = list(
        csv.reader(
            open(file_path, 'r'), delimiter='/', skipinitialspace=True))
    for ri, row in enumerate(pbar(tsvin, task_str)):
        if row[0][0] == '#':
            ct = row[0].lstrip('#')
            continue
        name = row[0]
        (name, source) = catalog.new_entry(name, bibcode='2016ApJ...832..108M')
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
            system = 'Vega'

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

    # 2013MNRAS.432L..90B
    file_path = os.path.join(catalog.get_current_task_repo(),
                             'ASCII/2013MNRAS.432L..90B.tsv')
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
            bibcode='2013MNRAS.432L..90B')
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
                [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
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
                [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                row[3],
                source,
                kind='host')
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

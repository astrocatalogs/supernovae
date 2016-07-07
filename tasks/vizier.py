"""Import tasks from the catalog available on VizieR.
"""
import csv
import os
from math import isnan

from astropy.time import Time as astrotime
from astroquery.vizier import Vizier

from astrocats.catalog.utils import (convert_aq_output, get_sig_digits,
                                     is_number, jd_to_mjd, make_date_string,
                                     pbar, pretty_num, rep_chars, round_sig,
                                     uniq_cdl)
from astrocats.supernovae.utils import radec_clean
from cdecimal import Decimal

from ..constants import CLIGHT, KM


def do_vizier(catalog):
    """
    """
    task_str = catalog.get_current_task_str()

    Vizier.ROW_LIMIT = -1

    # 2012ApJS..200...12H
    result = Vizier.get_catalogs('J/ApJS/200/12/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        name = row['SN']
        if is_number(name[:4]):
            name = 'SN' + name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJS..200...12H')
        catalog.entries[name].add_quantity('alias', name, source)
        if '[' not in row['Gal']:
            catalog.entries[name].add_quantity(
                'host', row['Gal'].replace('_', ' '), source)
        catalog.entries[name].add_quantity('redshift', str(
            row['z']), source, kind='heliocentric')
        catalog.entries[name].add_quantity('redshift', str(
            row['zCMB']), source, kind='cmb')
        catalog.entries[name].add_quantity('ebv', str(
            row['E_B-V_']), source, error=str(row['e_E_B-V_']) if
            row['e_E_B-V_'] else '')
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)

    # 2012ApJ...746...85S
    result = Vizier.get_catalogs('J/ApJ/746/85/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        name = row['Name'].replace('SCP', 'SCP-')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJ...746...85S')
        catalog.entries[name].add_quantity('alias', name, source)
        if row['f_Name']:
            catalog.entries[name].add_quantity('claimedtype', 'Ia', source)
        if row['z']:
            catalog.entries[name].add_quantity('redshift', str(
                row['z']), source, kind='spectroscopic')
        else:
            catalog.entries[name].add_quantity('redshift', str(
                row['zCl']), source, kind='cluster')
        catalog.entries[name].add_quantity('ebv', str(row['E_B-V_']), source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)

    result = Vizier.get_catalogs('J/ApJ/746/85/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        name = row['Name'].replace('SCP', 'SCP-')
        flux = Decimal(float(row['Flux']))
        if flux <= 0.0:
            continue
        err = Decimal(float(row['e_Flux']))
        zp = Decimal(float(row['Zero']))
        sig = get_sig_digits(str(row['Flux'])) + 1
        magnitude = pretty_num(zp - Decimal(2.5) * (flux.log10()), sig=sig)
        e_magnitude = pretty_num(
            Decimal(2.5) * (Decimal(1.0) + err / flux).log10(), sig=sig)
        if float(e_magnitude) > 5.0:
            continue
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJ...746...85S')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_photometry(
            time=str(row['MJD']), band=row['Filter'],
            instrument=row['Inst'],
            magnitude=magnitude, e_magnitude=e_magnitude, source=source)

    # 2004ApJ...602..571B
    result = Vizier.get_catalogs('J/ApJ/602/571/table8')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        name = 'SN' + row['SN']
        flux = Decimal(float(row['Flux']))
        if flux <= 0.0:
            continue
        err = Decimal(float(row['e_Flux']))
        sig = get_sig_digits(str(row['Flux'])) + 1
        magnitude = pretty_num(Decimal(25.0) - Decimal(2.5) * (flux.log10()),
                               sig=sig)
        e_magnitude = pretty_num(
            Decimal(2.5) * (Decimal(1.0) + err / flux).log10(), sig=sig)
        if float(e_magnitude) > 5.0:
            continue
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2004ApJ...602..571B')
        catalog.entries[name].add_quantity('alias', name, source)
        band = row['Filt']
        system = ''
        telescope = ''
        if band in ['R', 'I']:
            system = 'Cousins'
        if band == 'Z':
            telescope = 'Subaru'
        catalog.entries[name].add_photometry(
            time=str(row['MJD']), band=band, system=system,
            telescope=telescope,
            magnitude=magnitude, e_magnitude=e_magnitude, source=source)

    # 2014MNRAS.444.3258M
    result = Vizier.get_catalogs('J/MNRAS/444/3258/SNe')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        name = row['SN']
        if name == oldname:
            continue
        oldname = name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.444.3258M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('redshift', str(
            row['z']), source, kind='heliocentric', error=str(row['e_z']))
        catalog.entries[name].add_quantity(
            'ra', str(row['_RA']), source, unit='floatdegrees')
        catalog.entries[name].add_quantity('dec', str(
            row['_DE']), source, unit='floatdegrees')
    catalog.journal_entries()

    # 2014MNRAS.438.1391P
    result = Vizier.get_catalogs('J/MNRAS/438/1391/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.438.1391P')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('redshift', str(
            row['zh']), source, kind='heliocentric')
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
    catalog.journal_entries()

    # 2012ApJ...749...18B
    result = Vizier.get_catalogs('J/ApJ/749/18/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = row['Name'].replace(' ', '')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJ...749...18B')
        catalog.entries[name].add_quantity('alias', name, source)
        mjd = str(astrotime(2450000. + row['JD'], format='jd').mjd)
        band = row['Filt']
        magnitude = str(row['mag'])
        e_magnitude = str(row['e_mag'])
        e_magnitude = '' if e_magnitude == '--' else e_magnitude
        upperlimit = True if row['l_mag'] == '>' else False
        catalog.entries[name].add_photometry(
            time=mjd, band=band, magnitude=magnitude,
            e_magnitude=e_magnitude, instrument='UVOT',
            source=source, upperlimit=upperlimit, telescope='Swift',
            system='Swift')
    catalog.journal_entries()

    # 2010A&A...523A...7G
    result = Vizier.get_catalogs('J/A+A/523/A7/table9')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = 'SNLS-' + row['SNLS']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010A&A...523A...7G')
        catalog.entries[name].add_quantity('alias', name, source)
        astrot = astrotime(2450000. + row['Date1'], format='jd').datetime
        catalog.entries[name].add_quantity('discoverdate', make_date_string(
            astrot.year, astrot.month, astrot.day), source)
        catalog.entries[name].add_quantity('ebv', str(row['E_B-V_']), source)
        catalog.entries[name].add_quantity('redshift', str(
            row['z']), source, kind='heliocentric')
        type_str = (row['Type']
                    .replace('*', '?').replace('SN', '')
                    .replace('(pec)', ' P').replace('Ia? P?', 'Ia P?'))
        catalog.entries[name].add_quantity('claimedtype', type_str, source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
    catalog.journal_entries()

    # 2004A&A...415..863G
    result = Vizier.get_catalogs('J/A+A/415/863/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = 'SN' + row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2004A&A...415..863G')
        catalog.entries[name].add_quantity('alias', name, source)
        datesplit = row['Date'].split('-')
        date_str = make_date_string(datesplit[0], datesplit[1].lstrip('0'),
                                    datesplit[2].lstrip('0'))
        catalog.entries[name].add_quantity('discoverdate', date_str, source)
        catalog.entries[name].add_quantity(
            'host', 'Abell ' + str(row['Abell']), source)
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        if row['zSN']:
            catalog.entries[name].add_quantity('redshift', str(
                row['zSN']), source, kind='spectroscopic')
        else:
            catalog.entries[name].add_quantity('redshift', str(
                row['zCl']), source, kind='cluster')
    catalog.journal_entries()

    # 2008AJ....136.2306H
    result = Vizier.get_catalogs('J/AJ/136/2306/sources')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = 'SDSS-II SN ' + str(row['SNID'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2008AJ....136.2306H')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'claimedtype', row['SpType'].replace('SN.', '').strip(':'), source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)

    # 2010ApJ...708..661D
    result = Vizier.get_catalogs('J/ApJ/708/661/sn')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = row['SN']
        if not name:
            name = 'SDSS-II SN ' + str(row['SDSS-II'])
        else:
            name = 'SN' + name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010ApJ...708..661D')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'alias', 'SDSS-II ' + str(row['SDSS-II']), source)
        catalog.entries[name].add_quantity('claimedtype', 'II P', source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)

    result = Vizier.get_catalogs('J/ApJ/708/661/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        if row['f_SN'] == 'a':
            name = 'SDSS-II ' + str(row['SN'])
        else:
            name = 'SN' + row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010ApJ...708..661D')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('redshift', str(
            row['z']), source, error=str(row['e_z']))
    catalog.journal_entries()

    # 2014ApJ...795...44R
    result = Vizier.get_catalogs('J/ApJ/795/44/ps1_snIa')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...795...44R')
        catalog.entries[name].add_quantity('alias', name, source)
        astrot = astrotime(row['tdisc'], format='mjd').datetime
        catalog.entries[name].add_quantity('discoverdate',  make_date_string(
            astrot.year, astrot.month, astrot.day), source)
        catalog.entries[name].add_quantity('redshift', str(
            row['z']), source, error=str(row['e_z']), kind='heliocentric')
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity('claimedtype', 'Ia', source)

    result = Vizier.get_catalogs('J/ApJ/795/44/table6')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...795...44R')
        catalog.entries[name].add_quantity('alias', name, source)
        if row['mag'] != '--':
            catalog.entries[name].add_photometry(
                time=str(row['MJD']), band=row['Filt'],
                magnitude=str(row['mag']),
                e_magnitude=str(row['e_mag']), source=source, system='AB',
                telescope='PS1', instrument='PS1')
    catalog.journal_entries()

    # 1990A&AS...82..145C
    result = Vizier.get_catalogs('II/189/mag')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)

    with open(os.path.join(
            catalog.get_current_task_repo(), 'II_189_refs.csv')) as f:
        tsvin = csv.reader(f, delimiter='\t', skipinitialspace=True)
        ii189bibdict = {}
        ii189refdict = {}
        for r, row in enumerate(tsvin):
            if row[0] != '0':
                ii189bibdict[r + 1] = row[1]
            else:
                ii189refdict[r + 1] = row[2]

    for row in pbar(table, task_str):
        if row['band'][0] == '(':
            continue
        oldname = 'SN' + row['SN']
        name = catalog.add_entry(oldname)
        source = ''
        secsource = catalog.entries[name].add_source(
            bibcode='1990A&AS...82..145C', secondary=True)
        mjd = str(jd_to_mjd(Decimal(row['JD'])))
        mag = str(row['m'])
        band = row['band'].strip("'")
        if row['r_m'] in ii189bibdict:
            source = catalog.entries[name].add_source(
                bibcode=ii189bibdict[row['r_m']])
        else:
            source = catalog.entries[name].add_source(
                name=ii189refdict[row['r_m']])
        catalog.entries[name].add_quantity('alias', oldname, source)

        catalog.entries[name].add_photometry(
            time=mjd, band=band, magnitude=mag,
            source=uniq_cdl([source, secsource]))
    catalog.journal_entries()

    # 2014yCat.7272....0G
    result = Vizier.get_catalogs('VII/272/snrs')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)

    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = ''
        if row['Names']:
            names = row['Names'].split(',')
            for nam in names:
                if nam.strip()[:2] == 'SN':
                    name = nam.strip()
                    if is_number(name[2:]):
                        name = name + 'A'
            if not name:
                for nam in names:
                    if nam.strip('()') == nam:
                        name = nam.strip()
                        break
        if not name:
            name = row['SNR'].strip()

        oldname = name
        name = catalog.add_entry(oldname)
        source = (catalog.entries[name]
                  .add_source(bibcode='2014BASI...42...47G') +
                  ',' +
                  (catalog.entries[name]
                   .add_source(name='Galactic SNRs',
                               url=('https://www.mrao.cam.ac.uk/'
                                    'surveys/snrs/snrs.data.html'))))
        catalog.entries[name].add_quantity('alias', oldname, source)

        catalog.entries[name].add_quantity('alias', row['SNR'].strip(), source)
        catalog.entries[name].add_quantity(
            'alias', 'MWSNR ' + row['SNR'].strip('G '), source)

        if row['Names']:
            names = row['Names'].split(',')
            for nam in names:
                catalog.entries[name].add_quantity('alias', nam.replace(
                    'Vela (XYZ)', 'Vela').strip('()').strip(), source)
                if nam.strip()[:2] == 'SN':
                    catalog.entries[name].add_quantity(
                        'discoverdate', nam.strip()[2:], source)

        catalog.entries[name].add_quantity('host', 'Milky Way', source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
    catalog.journal_entries()

    # 2014MNRAS.442..844F
    result = Vizier.get_catalogs('J/MNRAS/442/844/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SN' + row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.442..844F')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('redshift', str(
            row['zhost']), source, kind='host')
        catalog.entries[name].add_quantity('ebv', str(row['E_B-V_']), source)
    catalog.journal_entries()

    result = Vizier.get_catalogs('J/MNRAS/442/844/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    instr = 'KAIT'
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SN' + str(row['SN'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.442..844F')
        catalog.entries[name].add_quantity('alias', name, source)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row['MJD'], band=band, magnitude=row[bandtag],
                    e_magnitude=row['e_' + bandtag], source=source,
                    telescope=instr, instrument=instr)
    catalog.journal_entries()

    # 2012MNRAS.425.1789S
    result = Vizier.get_catalogs('J/MNRAS/425/1789/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = ''.join(row['SimbadName'].split(' '))
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012MNRAS.425.1789S')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('alias', 'SN' + row['SN'], source)
        catalog.entries[name].add_quantity('host', row['Gal'], source)
        if is_number(row['cz']):
            red_str = str(
                round_sig(float(row['cz']) * KM / CLIGHT,
                          sig=get_sig_digits(str(row['cz']))))
            catalog.entries[name].add_quantity(
                'redshift', red_str, source, kind='heliocentric')
        catalog.entries[name].add_quantity('ebv', str(row['E_B-V_']), source)
    catalog.journal_entries()

    # 2015ApJS..219...13W
    result = Vizier.get_catalogs('J/ApJS/219/13/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = u'LSQ' + str(row['LSQ'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015ApJS..219...13W')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source,
            error=row['e_z'], kind='heliocentric')
        catalog.entries[name].add_quantity('ebv', row['E_B-V_'], source)
        catalog.entries[name].add_quantity('claimedtype', 'Ia', source)
    result = Vizier.get_catalogs('J/ApJS/219/13/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'LSQ' + row['LSQ']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015ApJS..219...13W')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_photometry(
            time=str(jd_to_mjd(Decimal(row['JD']))),
            instrument='QUEST',
            observatory='La Silla', band=row['Filt'], telescope='ESO Schmidt',
            magnitude=row['mag'], e_magnitude=row['e_mag'], system='Swope',
            source=source)
    catalog.journal_entries()

    # 2012Natur.491..228C
    result = Vizier.get_catalogs('J/other/Nat/491.228/tablef1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN2213-1745'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012Natur.491..228C')
    catalog.entries[name].add_quantity('alias', name, source)
    catalog.entries[name].add_quantity('claimedtype', 'SLSN-R', source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['g', 'r', 'i']:
            bandtag = band + '_mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row['MJD' + band + '_'], band=band + "'",
                    magnitude=row[bandtag], e_magnitude=row['e_' + bandtag],
                    source=source)

    result = Vizier.get_catalogs('J/other/Nat/491.228/tablef2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN1000+0216'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012Natur.491..228C')
    catalog.entries[name].add_quantity('alias', name, source)
    catalog.entries[name].add_quantity('claimedtype', 'SLSN-II?', source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['g', 'r', 'i']:
            bandtag = band + '_mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row['MJD' + band + '_'], band=band + "'",
                    magnitude=row[bandtag], e_magnitude=row['e_' + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2011Natur.474..484Q
    result = Vizier.get_catalogs('J/other/Nat/474.484/tables1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2011Natur.474..484Q')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_photometry(
            time=row['MJD'], band=row['Filt'], telescope=row['Tel'],
            magnitude=row['mag'], e_magnitude=row['e_mag'], source=source)
    catalog.journal_entries()

    # 2011ApJ...736..159G
    result = Vizier.get_catalogs('J/ApJ/736/159/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PTF10vdl'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...736..159G')
    catalog.entries[name].add_quantity('alias', name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        catalog.entries[name].add_photometry(
            time=str(jd_to_mjd(Decimal(row['JD']))),
            band=row['Filt'],
            telescope=row['Tel'], magnitude=row['mag'],
            e_magnitude=row['e_mag'] if is_number(row['e_mag']) else '',
            upperlimit=(not is_number(row['e_mag'])), source=source)
    catalog.journal_entries()

    # 2012ApJ...760L..33B
    result = Vizier.get_catalogs('J/ApJ/760/L33/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PTF12gzk'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012ApJ...760L..33B')
    catalog.entries[name].add_quantity('alias', name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        # Fixing a typo in VizieR table
        if str(row['JD']) == '2455151.456':
            row['JD'] = '2456151.456'
        catalog.entries[name].add_photometry(
            time=str(jd_to_mjd(Decimal(row['JD']))),
            band=row['Filt'],
            telescope=row['Inst'], magnitude=row['mag'],
            e_magnitude=row['e_mag'], source=source)
    catalog.journal_entries()

    # 2013ApJ...769...39S
    result = Vizier.get_catalogs('J/ApJ/769/39/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PS1-12sk'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013ApJ...769...39S')
    catalog.entries[name].add_quantity('alias', name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        instrument = ''
        telescope = ''
        if row['Inst'] == 'RATCam':
            instrument = row['Inst']
        else:
            telescope = row['Inst']
        catalog.entries[name].add_photometry(
            time=row['MJD'], band=row['Filt'], telescope=telescope,
            instrument=instrument, magnitude=row['mag'],
            e_magnitude=row['e_mag'] if not row['l_mag'] else '',
            upperlimit=(row['l_mag'] == '>'), source=source)
    catalog.journal_entries()

    # 2009MNRAS.394.2266P
    # Note: Instrument info available via links in VizieR, can't auto-parse
    # just yet.
    name = 'SN2005cs'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2009MNRAS.394.2266P')
    catalog.entries[name].add_quantity('alias', name, source)
    result = Vizier.get_catalogs('J/MNRAS/394/2266/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['U', 'B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                e_mag = (row['e_' + bandtag]
                         if row['l_' + bandtag] != '>' else '')
                upl = row['l_' + bandtag] == '>'
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row['JD']))),
                    band=band,
                    magnitude=row[bandtag], e_magnitude=e_mag,
                    source=source, upperlimit=upl)
        if ('zmag' in row and is_number(row['zmag']) and not
                isnan(float(row['zmag']))):
            catalog.entries[name].add_photometry(
                time=str(jd_to_mjd(Decimal(row['JD']))),
                band='z',
                magnitude=row['zmag'], e_magnitude=row['e_zmag'],
                source=source)

    result = Vizier.get_catalogs('J/MNRAS/394/2266/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                time = str(jd_to_mjd(Decimal(row['JD'])))
                e_mag = (row['e_' + bandtag]
                         if row['l_' + bandtag] != '>' else '')
                catalog.entries[name].add_photometry(
                    time=time, band=band, magnitude=row[bandtag],
                    e_magnitude=e_mag, source=source,
                    upperlimit=(row['l_' + bandtag] == '>'))

    result = Vizier.get_catalogs('J/MNRAS/394/2266/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['J', 'H', 'K']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row['JD']))),
                    band=band, magnitude=row[bandtag],
                    e_magnitude=row['e_' + bandtag], source=source)
    catalog.journal_entries()

    # 2013AJ....145...99A
    result = Vizier.get_catalogs('J/AJ/145/99/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN2003ie'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013AJ....145...99A')
    catalog.entries[name].add_quantity('alias', name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'R']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row["MJD"], band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag] if
                    not row["l_" + bandtag] else '',
                    upperlimit=(row['l_' + bandtag] == '>'),
                    source=source)
        for band in ['V', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row["MJD"], band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag] if
                    is_number(row["e_" + bandtag]) else '',
                    upperlimit=(not is_number(row["e_" + bandtag])),
                    source=source)
    catalog.journal_entries()

    # 2011ApJ...729..143C
    name = 'SN2008am'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...729..143C')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/ApJ/729/143/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        e_mag = row['e_mag'] if not row['l_mag'] else ''
        catalog.entries[name].add_photometry(
            time=row['MJD'], band='ROTSE', telescope='ROTSE',
            magnitude=row['mag'], e_magnitude=e_mag,
            upperlimit=(row['l_mag'] == '<'), source=source)

    result = Vizier.get_catalogs('J/ApJ/729/143/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['J', 'H', 'Ks']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row["MJD"],
                    telescope="PAIRITEL", band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/ApJ/729/143/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        catalog.entries[name].add_photometry(
            time=row['MJD'], band=row['Filt'], telescope='P60',
            magnitude=row['mag'], e_magnitude=row['e_mag'], source=source)

    result = Vizier.get_catalogs('J/ApJ/729/143/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        catalog.entries[name].add_photometry(
            time=row['MJD'], band=row['Filt'], instrument='UVOT',
            telescope='Swift',
            magnitude=row['mag'], e_magnitude=row['e_mag'], source=source)
    catalog.journal_entries()

    # 2011ApJ...728...14P
    name = 'SN2009bb'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...728...14P')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row["JD"]))),
                    telescope=row["Tel"], band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['u', 'g', 'r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row["JD"]))),
                    telescope=row["Tel"], band=band + "'",
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['Y', 'J', 'H']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row["JD"]))),
                    instrument=row['Inst'], band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)
    catalog.journal_entries()

    # 2011PAZh...37..837T
    name = 'SN2009nr'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011PAZh...37..837T')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/PAZh/37/837/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + 2455000))
        for band in ['U', 'B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope=row["Tel"], band=band,
                    magnitude=row[bandtag], e_magnitude=row["e_" + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2013MNRAS.433.1871B
    name = 'SN2012aw'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013MNRAS.433.1871B')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/MNRAS/433/1871/table3a')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + 2456000))
        for band in ['U', 'B', 'V', 'Rc', 'Ic']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope=row["Tel"],
                    band=band, magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/MNRAS/433/1871/table3b')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + 2456000))
        for band in ['g', 'r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope=row["Tel"],
                    band=band, magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)
    catalog.journal_entries()

    # 2014AJ....148....1Z
    name = 'SN2012fr'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2014AJ....148....1Z')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/AJ/148/1/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope="LJT",
                    instrument="YFOSC", band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/AJ/148/1/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['U', 'B', 'V', 'UVW1', 'UVW2', 'UVM2']:
            bandtag = band + 'mag' if len(band) == 1 else band
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope="Swift",
                    instrument="UVOT", band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)

    result = Vizier.get_catalogs('J/AJ/148/1/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd, telescope="LJT",
                    band=band, magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag], source=source)
    catalog.journal_entries()

    # 2015ApJ...805...74B
    name = 'SN2014J'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2014AJ....148....1Z')
    catalog.entries[name].add_quantity('alias', name, source)

    result = Vizier.get_catalogs('J/ApJ/805/74/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        if ('mag' in row and is_number(row['mag']) and not
                isnan(float(row['mag']))):
            catalog.entries[name].add_photometry(
                time=mjd, telescope='Swift',
                instrument='UVOT', band=row['Filt'],
                magnitude=row['mag'],
                e_magnitude=row['e_mag'], source=source)
        elif ('maglim' in row and is_number(row['maglim']) and not
              isnan(float(row['maglim']))):
            catalog.entries[name].add_photometry(
                time=mjd, telescope='Swift',
                instrument='UVOT', band=row['Filt'],
                magnitude=row['maglim'],
                upperlimit=True, source=source)
    catalog.journal_entries()

    # 2011ApJ...741...97D
    result = Vizier.get_catalogs('J/ApJ/741/97/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['SN'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2011ApJ...741...97D')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_photometry(
            time=str(jd_to_mjd(Decimal(row['JD']))),
            band=row['Filt'], magnitude=row['mag'],
            e_magnitude=row['e_mag'] if
            is_number(row['e_mag']) else '',
            upperlimit=(not is_number(row['e_mag'])), source=source)
    catalog.journal_entries()

    # 2015MNRAS.448.1206M
    # Note: Photometry from two SN can also be added from this source.
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity('claimedtype', 'Ia', source)
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['zph'], source, error=row['e_zph'],
            kind='photometric')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity('claimedtype', 'Ia?', source)
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table6')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
    result = Vizier.get_catalogs('J/MNRAS/448/1206/tablea2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity(
            'claimedtype', row['Typesoft'] + '?', source)
        catalog.entries[name].add_quantity(
            'claimedtype', row['Typepsnid'] + '?', source)
    result = Vizier.get_catalogs('J/MNRAS/448/1206/tablea3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = str(row['Name'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + name[4:6], source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'maxappmag', row['rP1mag'], source, error=row['e_rP1mag'])
        catalog.entries[name].add_quantity('maxband', 'r', source)
        catalog.entries[name].add_quantity('claimedtype', 'Candidate', source)
    catalog.journal_entries()

    # 2012AJ....143..126B
    result = Vizier.get_catalogs('J/AJ/143/126/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        if not row['Wcl'] or row['Wcl'] == 'N':
            continue
        row = convert_aq_output(row)
        name = str(row['SN']).replace(' ', '')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012AJ....143..126B')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'claimedtype', 'Ia-' + row['Wcl'], source)
    catalog.journal_entries()

    # 2015ApJS..220....9F
    for viztab in ['1', '2']:
        result = Vizier.get_catalogs('J/ApJS/220/9/table' + viztab)
        table = result[list(result.keys())[0]]
        table.convert_bytestring_to_unicode(python3_only=True)
        for row in pbar(table, task_str):
            row = convert_aq_output(row)
            name = catalog.add_entry(name=row['SN'])
            source = catalog.entries[name].add_source(
                bibcode='2015ApJS..220....9F')
            catalog.entries[name].add_quantity('alias', name, source)
            catalog.entries[name].add_quantity(
                'claimedtype', row['Type'], source)
            catalog.entries[name].add_quantity(
                'ra', row['RAJ2000'], source, unit='floatdegrees')
            catalog.entries[name].add_quantity(
                'dec', row['DEJ2000'], source, unit='floatdegrees')
            if '?' not in row['Host']:
                catalog.entries[name].add_quantity(
                    'host', row['Host'].replace('_', ' '), source)
            kind = ''
            if 'Host' in row['n_z']:
                kind = 'host'
            elif 'Spectrum' in row['n_z']:
                kind = 'spectroscopic'
            catalog.entries[name].add_quantity(
                'redshift', row['z'], source, error=row['e_z'], kind=kind)

    result = Vizier.get_catalogs('J/ApJS/220/9/table8')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = catalog.add_entry(row['SN'])
        source = catalog.entries[name].add_source(
            bibcode='2015ApJS..220....9F')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
        catalog.entries[name].add_photometry(
            time=row['MJD'], band=row['Band'], magnitude=row['mag'],
            e_magnitude=row['e_mag'], telescope=row['Tel'], source=source)
    catalog.journal_entries()

    result = Vizier.get_catalogs('J/ApJ/673/999/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = catalog.add_entry(name='SN' + row['SN'])
        source = catalog.entries[name].add_source(
            bibcode='2008ApJ...673..999P')
        catalog.entries[name].add_quantity('alias', name, source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, kind='host')
        catalog.entries[name].add_quantity(
            'hostra', row['RAGdeg'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'hostdec', row['DEGdeg'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'claimedtype', row['Type'].strip(':'), source)
    catalog.journal_entries()

    # 2011MNRAS.417..916G
    result = Vizier.get_catalogs("J/MNRAS/417/916/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SNSDF' + row['SNSDF'],
            bibcode="2011MNRAS.417..916G")
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'redshift', row['zsp'] if row['zsp'] else row['zph'], source,
            kind='host')
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + row['SNSDF'][:2] + '/' + row['SNSDF'][2:4],
            source, kind='host')
        catalog.entries[name].add_quantity(
            'hostoffsetang', row['Offset'], source, unit='arcseconds')
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
    catalog.journal_entries()

    # 2013MNRAS.430.1746G
    result = Vizier.get_catalogs("J/MNRAS/430/1746/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SDSS' + row['SDSS'],
            bibcode="2013MNRAS.430.1746G")
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'discoverdate', row['Date'].replace('-', '/'), source)
        catalog.entries[name].add_quantity('redshift', row['z'], source)
        catalog.entries[name].add_quantity('claimedtype', row['Type'], source)
    catalog.journal_entries()

    # 2014AJ....148...13R
    result = Vizier.get_catalogs("J/AJ/148/13/high_z")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['Name'],
            bibcode="2014AJ....148...13R")
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + row['Name'][3:5], source)
        catalog.entries[name].add_quantity(
            'redshift', row['zSN'], source, kind='heliocentric',
            error=row['e_zSN'])
        catalog.entries[name].add_quantity('hostra', row['RAG'], source)
        catalog.entries[name].add_quantity('hostdec', row['DEG'], source)
        catalog.entries[name].add_quantity(
            'hostoffsetang', row['ASep'], source, unit='arcseconds')
        catalog.entries[name].add_quantity(
            'redshift', row['zhost'], source, kind='host',
            error=row['e_zhost'])
    result = Vizier.get_catalogs("J/AJ/148/13/low_z")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['Name'],
            bibcode="2014AJ....148...13R")
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'discoverdate', '20' + row['Name'][3:5], source)
        catalog.entries[name].add_quantity(
            'redshift', row['zSN'], source, kind='heliocentric',
            error=row['e_zSN'])
        catalog.entries[name].add_quantity('hostra', row['RAG'], source)
        catalog.entries[name].add_quantity('hostdec', row['DEG'], source)
        catalog.entries[name].add_quantity(
            'hostoffsetang', row['ASep'], source, unit='arcseconds')
        catalog.entries[name].add_quantity(
            'redshift', row['zhost'], source, kind='host',
            error=row['e_zhost'])
    catalog.journal_entries()

    # 2007ApJ...666..674M
    result = Vizier.get_catalogs("J/ApJ/666/674/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        essname = 'ESSENCE ' + row['ESSENCE']
        if row['SN']:
            name = 'SN' + row['SN']
        else:
            name = essname
        name, source = catalog.new_entry(
            name, bibcode="2007ApJ...666..674M")
        catalog.entries[name].add_quantity('alias', essname, source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'redshift', row['zSN'], source, error=row['e_zSN'],
            kind='heliocentric')
        catalog.entries[name].add_quantity(
            'redshift', row['zGal'], source, kind='host')
        catalog.entries[name].add_quantity(
            'claimedtype', row['SType'] if row['SType'] else row['Type'],
            source)
    catalog.journal_entries()

    # 2013AcA....63....1K
    result = Vizier.get_catalogs("J/AcA/63/1/table1")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        if 'OGLE' not in row['Name']:
            continue
        name, source = catalog.new_entry(
            row['Name'],
            bibcode="2013AcA....63....1K")
        catalog.entries[name].add_quantity('alias', row['OGLEIV'], source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        astrot = astrotime(float(row['Tmax']), format='jd').datetime
        catalog.entries[name].add_quantity('maxdate', make_date_string(
            astrot.year, astrot.month, astrot.day), source)
    catalog.journal_entries()

    # 2011MNRAS.410.1262W
    result = Vizier.get_catalogs("J/MNRAS/410/1262/tablea2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SNLS-' + row['SN'],
            bibcode="2011MNRAS.410.1262W")
        catalog.entries[name].add_quantity(
            'ra', row['_RA'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['_DE'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, error=row['e_z'],
            kind='heliocentric')
    catalog.journal_entries()

    # 2012ApJ...755...61S
    result = Vizier.get_catalogs("J/ApJ/755/61/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        sdssname = 'SDSS-II SN ' + row['SNID']
        if row['SN']:
            name = 'SN' + row['SN']
        else:
            name = sdssname
        name, source = catalog.new_entry(
            name, bibcode="2012ApJ...755...61S")
        err = row['e_z'] if is_number(row['e_z']) else ''
        catalog.entries[name].add_quantity('alias', sdssname, source)
        catalog.entries[name].add_quantity('hostra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('hostdec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, error=err, kind='host')
    catalog.journal_entries()

    # 2008AJ....135..348S
    result = Vizier.get_catalogs("J/AJ/135/348/SNe")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        sdssname = 'SDSS-II SN ' + row['SNID']
        if row['SN']:
            name = 'SN' + row['SN']
        else:
            name = sdssname
        name, source = catalog.new_entry(
            name, bibcode="2008AJ....135..348S")
        catalog.entries[name].add_quantity('alias', sdssname, source)
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal(360.0) + fra
        catalog.entries[name].add_quantity(
            'ra', str(fra), source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            'claimedtype', row['Type'].replace('SN', '').strip(), source)
    catalog.journal_entries()

    # 2010ApJ...713.1026D
    result = Vizier.get_catalogs("J/ApJ/713/1026/SNe")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        sdssname = 'SDSS-II SN ' + row['ID']
        if row['IAU']:
            name = 'SN' + row['IAU']
        else:
            name = sdssname
        name, source = catalog.new_entry(
            name, bibcode="2010ApJ...713.1026D")
        catalog.entries[name].add_quantity('alias', sdssname, source)
        catalog.entries[name].add_quantity(
            'ra', row['RAJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, kind='heliocentric')
    catalog.journal_entries()

    # 2013ApJ...770..107C
    result = Vizier.get_catalogs("J/ApJ/770/107/galaxies")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['SN'], bibcode="2013ApJ...770..107C")
        catalog.entries[name].add_quantity('hostra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('hostdec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source,
            error=row['e_z'] if is_number(row['e_z']) else '', kind='host')
    catalog.journal_entries()

    # 2011ApJ...738..162S
    result = Vizier.get_catalogs("J/ApJ/738/162/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SDSS-II SN ' + row['CID']
        name, source = catalog.new_entry(
            name, bibcode="2011ApJ...738..162S")
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal(360.0) + fra
        catalog.entries[name].add_quantity(
            'ra', str(fra), source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, kind='spectroscopic',
            error=row['e_z'])
        catalog.entries[name].add_quantity(
            'claimedtype', 'Ia', source, probability=row['PzIa'])
    result = Vizier.get_catalogs("J/ApJ/738/162/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SDSS-II SN ' + row['CID']
        name, source = catalog.new_entry(
            name, bibcode="2011ApJ...738..162S")
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal(360.0) + fra
        catalog.entries[name].add_quantity(
            'ra', str(fra), source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'dec', row['DEJ2000'], source, unit='floatdegrees')
        catalog.entries[name].add_quantity(
            'redshift', row['zph'], source, kind='photometric')
        catalog.entries[name].add_quantity(
            'claimedtype', 'Ia', source, probability=row['PIa'])
    catalog.journal_entries()

    # 2015MNRAS.446..943V
    snrtabs = ["ngc2403", "ngc2903", "ngc300", "ngc3077", "ngc4214", "ngc4395",
               "ngc4449", "ngc5204", "ngc5585", "ngc6946", "ngc7793", "m33",
               "m74", "m81", "m82", "m83", "m101", "m31"]
    for tab in pbar(snrtabs, task_str):
        result = Vizier.get_catalogs("J/MNRAS/446/943/" + tab)
        table = result[list(result.keys())[0]]
        table.convert_bytestring_to_unicode(python3_only=True)
        for ri, row in enumerate(pbar(table, task_str)):
            ra = (row['RAJ2000'] if isinstance(row['RAJ2000'], str) else
                  radec_clean(str(row['RAJ2000']), 'ra',
                              unit='floatdegrees')[0])
            dec = (row['DEJ2000'] if isinstance(row['DEJ2000'], str) else
                   radec_clean(str(row['DEJ2000']), 'dec',
                               unit='floatdegrees')[0])
            name = (tab.upper() + 'SNR J' + rep_chars(ra, ' :.') +
                    rep_chars(dec, ' :.'))
            name, source = catalog.new_entry(
                name, bibcode="2015MNRAS.446..943V")
            catalog.entries[name].add_quantity('ra', ra, source)
            catalog.entries[name].add_quantity('dec', dec, source)
            catalog.entries[name].add_quantity('host', tab.upper(), source)
    catalog.journal_entries()

    # 2009ApJ...703..370C
    result = Vizier.get_catalogs("J/ApJ/703/370/tables")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        ra = row['RAJ2000']
        dec = row['DEJ2000']
        name = row['Gal'].replace(' ', '') + 'SNR J' + \
            rep_chars(ra, ' .') + rep_chars(dec, ' .')
        name, source = catalog.new_entry(
            name, bibcode="2009ApJ...703..370C")
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        catalog.entries[name].add_quantity('host', row['Gal'], source)
    catalog.journal_entries()

    # 2016ApJ...821...57D
    name, source = catalog.new_entry(
        'SN2013ge', bibcode="2016ApJ...821...57D")
    result = Vizier.get_catalogs("J/ApJ/821/57/table1")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['UVW2', 'UVM2', 'UVW1', 'U', 'B', 'V']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(row["MJD"]), band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    telescope='Swift', instrument='UVOT',
                    source=source)
    result = Vizier.get_catalogs("J/ApJ/821/57/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(row["MJD"]), band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    instrument='CAO', source=source)
    result = Vizier.get_catalogs("J/ApJ/821/57/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', "r'", "i'"]:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(row["MJD"]), band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    instrument='FLWO', source=source)
    result = Vizier.get_catalogs("J/ApJ/821/57/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and not
                    isnan(float(row[bandtag]))):
                upp = False
                if "l_" + bandtag in row and row["l_" + bandtag] == ">":
                    upp = True
                catalog.entries[name].add_photometry(
                    time=str(row["MJD"]), band=band,
                    magnitude=row[bandtag], upperlimit=upp,
                    e_magnitude=row["e_" + bandtag] if
                    is_number(row["e_" + bandtag]) else '',
                    instrument=row["Inst"], source=source)
    catalog.journal_entries()

    # 2004ApJ...607..665R
    result = Vizier.get_catalogs("J/ApJ/607/665/table1")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(
            name, bibcode="2004ApJ...607..665R")
        catalog.entries[name].add_quantity('alias', row['OName'], source)
        catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
    result = Vizier.get_catalogs("J/ApJ/607/665/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(
            name, bibcode="2004ApJ...607..665R")
        mjd = str(jd_to_mjd(Decimal(row['HJD'])))
        catalog.entries[name].add_photometry(
            time=mjd, band=row['Filt'],
            magnitude=row['Vega'], system='Vega',
            e_magnitude=row['e_Vega'], source=source)
    result = Vizier.get_catalogs("J/ApJ/607/665/table5")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(
            name, bibcode="2004ApJ...607..665R")
        catalog.entries[name].add_quantity(
            'redshift', row['z'], source, kind='spectroscopic')
    catalog.journal_entries()

    return


def do_lennarz(catalog):
    """
    """
    task_str = catalog.get_current_task_str()
    Vizier.ROW_LIMIT = -1
    result = Vizier.get_catalogs('J/A+A/538/A120/usc')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)

    bibcode = '2012A&A...538A.120L'
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SN' + row['SN']
        name = catalog.add_entry(name)

        source = catalog.entries[name].add_source(bibcode=bibcode)
        catalog.entries[name].add_quantity('alias', name, source)

        if row['RAJ2000']:
            catalog.entries[name].add_quantity('ra', row['RAJ2000'], source)
        if row['DEJ2000']:
            catalog.entries[name].add_quantity('dec', row['DEJ2000'], source)
        if row['RAG']:
            catalog.entries[name].add_quantity('hostra', row['RAG'], source)
        if row['DEG']:
            catalog.entries[name].add_quantity('hostdec', row['DEG'], source)
        if row['Gal']:
            catalog.entries[name].add_quantity('host', row['Gal'], source)
        if row['Type']:
            claimedtypes = row['Type'].split('|')
            for claimedtype in claimedtypes:
                catalog.entries[name].add_quantity(
                    'claimedtype', claimedtype.strip(' -'), source)
        if row['z']:
            if name not in ['SN1985D', 'SN2004cq']:
                catalog.entries[name].add_quantity(
                    'redshift', row['z'], source, kind='host')
        if row['Dist']:
            if row['e_Dist']:
                catalog.entries[name].add_quantity(
                    'lumdist', row['Dist'], source,
                    error=row['e_Dist'], kind='host')
            else:
                catalog.entries[name].add_quantity(
                    'lumdist', row['Dist'], source, kind='host')

        if row['Ddate']:
            datestring = row['Ddate'].replace('-', '/')

            catalog.entries[name].add_quantity(
                'discoverdate', datestring, source)

            if 'photometry' not in catalog.entries[name]:
                if ('Dmag' in row and is_number(row['Dmag']) and not
                        isnan(float(row['Dmag']))):
                    datesplit = row['Ddate'].strip().split('-')
                    if len(datesplit) == 3:
                        datestr = row['Ddate'].strip()
                    elif len(datesplit) == 2:
                        datestr = row['Ddate'].strip() + '-01'
                    elif len(datesplit) == 1:
                        datestr = row['Ddate'].strip() + '-01-01'
                    mjd = str(astrotime(datestr).mjd)
                    catalog.entries[name].add_photometry(
                        time=mjd, band=row['Dband'], magnitude=row['Dmag'],
                        source=source)
        if row['Mdate']:
            datestring = row['Mdate'].replace('-', '/')

            catalog.entries[name].add_quantity('maxdate', datestring, source)

            if 'photometry' not in catalog.entries[name]:
                if ('MMag' in row and is_number(row['MMag']) and not
                        isnan(float(row['MMag']))):
                    datesplit = row['Mdate'].strip().split('-')
                    if len(datesplit) == 3:
                        datestr = row['Mdate'].strip()
                    elif len(datesplit) == 2:
                        datestr = row['Mdate'].strip() + '-01'
                    elif len(datesplit) == 1:
                        datestr = row['Mdate'].strip() + '-01-01'
                    mjd = str(astrotime(datestr).mjd)
                    catalog.entries[name].add_photometry(
                        time=mjd, band=row['Mband'],
                        magnitude=row['Mmag'], source=source)

    catalog.journal_entries()
    return

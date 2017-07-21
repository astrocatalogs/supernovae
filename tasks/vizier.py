"""Import tasks from the catalog available on VizieR.
"""
import csv
import os
from math import isnan

from astrocats.catalog.photometry import PHOTOMETRY, set_pd_mag_from_counts
from astrocats.catalog.quantity import QUANTITY
from astrocats.catalog.utils import (convert_aq_output, get_sig_digits,
                                     is_number, jd_to_mjd, make_date_string,
                                     pbar, rep_chars, round_sig, uniq_cdl)
from astropy.time import Time as astrotime
from astroquery.vizier import Vizier
from decimal import Decimal

from ..constants import CLIGHT, KM
from ..supernova import SUPERNOVA
from ..utils import radec_clean


def do_vizier(catalog):
    """
    """
    task_str = catalog.get_current_task_str()

    Vizier.ROW_LIMIT = -1
    Vizier.VIZIER_SERVER = 'vizier.cfa.harvard.edu'

    # 2008MNRAS.384..107E
    results = Vizier.get_catalogs([
        'J/MNRAS/384/107/table3', 'J/MNRAS/384/107/table5',
        'J/MNRAS/384/107/table4'
    ])
    for ti, table in enumerate(results):
        table.convert_bytestring_to_unicode(python3_only=True)
        (name, source) = catalog.new_entry(
            'SN2002cv', bibcode='2008MNRAS.384..107E')
        for row in pbar(table, task_str):
            row = convert_aq_output(row)
            bands = [
                x for x in row if x.endswith('mag') and not x.startswith('e_')
            ]
            for bandtag in bands:
                band = bandtag.replace('mag', '')
                if (bandtag in row and is_number(row[bandtag]) and
                        not isnan(float(row[bandtag]))):
                    photodict = {
                        PHOTOMETRY.TIME: jd_to_mjd(Decimal(str(row['JD']))),
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.BAND: band,
                        PHOTOMETRY.MAGNITUDE: row[bandtag],
                        PHOTOMETRY.SOURCE: source,
                        PHOTOMETRY.INSTRUMENT: row['Inst']
                    }
                    if ti == 2:
                        photodict[PHOTOMETRY.SCORRECTED] = True
                    if row.get('l_' + bandtag, '') in ['>', '>=']:
                        photodict[PHOTOMETRY.UPPER_LIMIT] = True
                    else:
                        if ('e_' + bandtag) in row:
                            photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_' +
                                                                    bandtag]
                    catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...824....6O
    result = Vizier.get_catalogs('J/ApJ/824/6/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    (name, source) = catalog.new_entry(
        'SN2015bh', bibcode='2016ApJ...824....6O')
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        bands = [
            x for x in row if x.endswith('mag') and not x.startswith('e_')
        ]
        for bandtag in bands:
            band = bandtag.replace('mag', '')
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row['MJD']),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.COUNT_RATE: str(row['Cts']),
                    PHOTOMETRY.E_COUNT_RATE: str(row['e_Cts']),
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                if row.get('l_' + bandtag, '') == '>':
                    photodict[PHOTOMETRY.UPPER_LIMIT] = True
                else:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_' + bandtag]
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016AJ....151..125Z
    result = Vizier.get_catalogs('J/AJ/151/125/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    (name, source) = catalog.new_entry(
        'SN2013dy', bibcode='2016AJ....151..125Z')
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        bands = [
            x for x in row if x.endswith('mag') and not x.startswith('e_')
        ]
        for bandtag in bands:
            band = bandtag.replace('mag', '')
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row['MJD']),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.TELESCOPE: row['Tel']
                }
                if row.get('l_' + bandtag, '') == '>':
                    photodict[PHOTOMETRY.UPPER_LIMIT] = True
                else:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = str(Decimal(
                        '0.01') * Decimal(row['e_' + bandtag]))
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016A&A...592..A40F
    result = Vizier.get_catalogs('J/A+A/592/A40/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        (name, source) = catalog.new_entry(
            row['Name'], bibcode='2016A&A...592..A40F')
        tel, filt = row['Filter'].split('_')
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.TELESCOPE: tel,
            PHOTOMETRY.BAND: filt,
            PHOTOMETRY.MAGNITUDE: row['Xmag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_Xmag'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016A&A...593A..68F
    results = Vizier.get_catalogs(
        ['J/A+A/593/A68/ph12os', 'J/A+A/593/A68/ph13bvn'])
    for ti, table in enumerate(results):
        table.convert_bytestring_to_unicode(python3_only=True)
        (name, source) = catalog.new_entry(
            ['PTF12os', 'iPTF13bvn'][ti], bibcode='2016A&A...593A..68F')
        for row in pbar(table, task_str):
            photodict = {
                PHOTOMETRY.TIME: jd_to_mjd(Decimal(str(row['JD']))),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TELESCOPE: row['Tel'],
                PHOTOMETRY.BAND: row['Filter'],
                PHOTOMETRY.MAGNITUDE: row['mag'],
                PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...825L..22F
    result = Vizier.get_catalogs('J/ApJ/825/L22/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    (name, source) = catalog.new_entry(
        'iPTF13bvn', bibcode='2016ApJ...825L..22F')
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        bands = [
            x for x in row if x.endswith('mag') and not x.startswith('e_')
        ]
        for bandtag in bands:
            band = bandtag.replace('mag', '')
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row['MJD']),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.TELESCOPE: row['Tel']
                }
                if row.get('l_' + bandtag, '') == '>':
                    photodict[PHOTOMETRY.UPPER_LIMIT] = True
                else:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_' + bandtag]
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...826..144S
    result = Vizier.get_catalogs('J/ApJ/826/144/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    (name, source) = catalog.new_entry(
        'ASASSN-14lp', bibcode='2016ApJ...826..144S')
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        photodict = {
            PHOTOMETRY.TIME:
            jd_to_mjd(Decimal(row['JD']) + Decimal('2450000')),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.BAND: row['Band'],
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.SOURCE: source
        }
        if row['l_mag'] == '>':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_mag']
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2012ApJ...756..173S
    results = Vizier.get_catalogs(
        ['J/ApJ/756/173/table2', 'J/ApJ/756/173/table3'])
    for ti, table in enumerate(results):
        table.convert_bytestring_to_unicode(python3_only=True)
        for row in pbar(table, task_str):
            row = convert_aq_output(row)
            name = row['SN']
            if is_number(name[:4]):
                name = 'SN' + name
            name, source = catalog.new_entry(
                name, bibcode='2012ApJ...756..173S')
            bands = [
                x for x in row if x.endswith('mag') and not x.startswith('e_')
            ]
            for bandtag in bands:
                band = bandtag.replace('mag', '')
                if (bandtag in row and is_number(row[bandtag]) and
                        not isnan(float(row[bandtag]))):
                    photodict = {
                        PHOTOMETRY.TIME: str(
                            jd_to_mjd(
                                Decimal(str(row['JD'])) + Decimal('2450000'))),
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.MAGNITUDE: row[bandtag],
                        PHOTOMETRY.SOURCE: source,
                        PHOTOMETRY.TELESCOPE: row['Tel']
                    }
                    photodict[PHOTOMETRY.BAND] = band
                    emag = '0.' + row['e_' + bandtag]
                    if is_number(emag) and not isnan(float(emag)):
                        photodict[PHOTOMETRY.E_MAGNITUDE] = emag
                    catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...819...35A
    result = Vizier.get_catalogs('J/ApJ/819/35/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['ID']
        (name, source) = catalog.new_entry(name, bibcode='2016ApJ...819...35A')
        photodict = {
            PHOTOMETRY.TIME: jd_to_mjd(Decimal(row['HJD'])),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.SOURCE: source
        }
        if row['l_mag'] == '>':
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        else:
            photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_mag']
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2013NewA...20...30M
    errdict = {'B': '0.011', 'V': '0.007', 'Rc': '0.010', 'Ic': '0.016'}
    snnames = ['SN2011fe', 'SN2012cg', 'SN2012aw']
    for sni in range(3):
        results = Vizier.get_catalogs('J/other/NewA/20.30/table' + str(sni +
                                                                       1))
        for ti, table in enumerate(results):
            table.convert_bytestring_to_unicode(python3_only=True)
            for row in pbar(table, task_str):
                row = convert_aq_output(row)
                name = snnames[sni]
                name, source = catalog.new_entry(
                    name, bibcode='2013NewA...20...30M')
                bands = [
                    x for x in row
                    if x.endswith('mag') and not x.startswith('e_')
                ]
                for bandtag in bands:
                    band = bandtag.replace('mag', '')
                    if (bandtag in row and is_number(row[bandtag]) and
                            not isnan(float(row[bandtag]))):
                        photodict = {
                            PHOTOMETRY.TIME: str(
                                jd_to_mjd(
                                    Decimal(str(row['JD'])) + Decimal(
                                        '2450000'))),
                            PHOTOMETRY.U_TIME: 'MJD',
                            PHOTOMETRY.MAGNITUDE: row[bandtag],
                            PHOTOMETRY.SOURCE: source,
                            PHOTOMETRY.TELESCOPE: row['Tel'],
                            PHOTOMETRY.SYSTEM: 'Vega',
                            PHOTOMETRY.BAND_SET: 'Johnson-Cousins',
                            PHOTOMETRY.BAND: band,
                            PHOTOMETRY.E_MAGNITUDE: errdict[band]
                        }
                        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2008ApJ...686..749K
    result = Vizier.get_catalogs('J/ApJ/686/749/table10')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['SN'], bibcode='2008ApJ...686..749K')
        bands = [
            x for x in row if x.endswith('mag') and not x.startswith('e_')
        ]
        for bandtag in bands:
            band = bandtag.replace('mag', '')
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: jd_to_mjd(Decimal(row['JD'])),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row['e_' + bandtag],
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.TELESCOPE: row['Tel']
                }
                catalog.entries[name].add_photometry(**photodict)
    result = Vizier.get_catalogs('J/ApJ/686/749/table12')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['SN'], bibcode='2008ApJ...686..749K')
        bands = [
            x for x in row if x.endswith('Flux') and not x.startswith('e_')
        ]
        for bandtag in bands:
            band = bandtag.replace('Flux', '')
            flux = str(row[bandtag])
            if not is_number(flux):
                continue
            err = str(row['e_' + bandtag])
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                zp = 30.0
                photodict = {
                    PHOTOMETRY.TIME: row['MJD-' + band],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.COUNT_RATE: str(flux),
                    PHOTOMETRY.E_COUNT_RATE: str(err),
                    PHOTOMETRY.ZERO_POINT: str(zp),
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.SURVEY: 'SCP'
                }
                set_pd_mag_from_counts(photodict, flux, ec=err, zp=zp)
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2013A&A...555A..10T
    results = Vizier.get_catalogs(
        ['J/A+A/555/A10/table4', 'J/A+A/555/A10/table5'])
    for ti, table in enumerate(results):
        table.convert_bytestring_to_unicode(python3_only=True)
        for row in pbar(table, task_str):
            row = convert_aq_output(row)
            name = row['SN']
            if is_number(name[:4]):
                name = 'SN' + name
            name, source = catalog.new_entry(
                name, bibcode='2013A&A...555A..10T')
            bands = [
                x for x in row if x.endswith('mag') and not x.startswith('e_')
            ]
            for bandtag in bands:
                band = bandtag.replace('mag', '')
                if (bandtag in row and is_number(row[bandtag]) and
                        not isnan(float(row[bandtag]))):
                    photodict = {
                        PHOTOMETRY.TIME: str(
                            jd_to_mjd(
                                Decimal(str(row['Epoch'])) + Decimal(
                                    '2453000'))),
                        PHOTOMETRY.U_TIME: 'MJD',
                        PHOTOMETRY.MAGNITUDE: row[bandtag],
                        PHOTOMETRY.SOURCE: source,
                        PHOTOMETRY.TELESCOPE: row['Tel']
                    }
                    if ti == 0:
                        photodict[PHOTOMETRY.BAND_SET] = 'SDSS'
                        photodict[PHOTOMETRY.SYSTEM] = 'SDSS'
                        band = band + "'"
                    photodict[PHOTOMETRY.BAND] = band
                    if (is_number(row['e_' + bandtag]) and
                            not isnan(float(row['e_' + bandtag]))):
                        photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_' + bandtag]
                    catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2016ApJ...820...33R
    result = Vizier.get_catalogs('J/ApJ/820/33/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        (name, source) = catalog.new_entry(name, bibcode='2016ApJ...820...33R')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['z']), source, kind='spectroscopic')

    result = Vizier.get_catalogs('J/ApJ/820/33/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        (name, source) = catalog.new_entry(name, bibcode='2016ApJ...820...33R')
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.SOURCE: source
        }
        if row['mag'] and is_number(row['mag']):
            photodict[PHOTOMETRY.MAGNITUDE] = row['mag']
            photodict[PHOTOMETRY.E_MAGNITUDE] = row['e_mag']
        else:
            photodict[PHOTOMETRY.MAGNITUDE] = row['Limit']
            photodict[PHOTOMETRY.UPPER_LIMIT] = True
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2012ApJS..200...12H
    result = Vizier.get_catalogs('J/ApJS/200/12/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        if is_number(name[:4]):
            name = 'SN' + name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJS..200...12H')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if '[' not in row['Gal']:
            catalog.entries[name].add_quantity(
                SUPERNOVA.HOST, row['Gal'].replace('_', ' '), source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['z']), source, kind='heliocentric')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['zCMB']), source, kind='cmb')
        catalog.entries[name].add_quantity(
            SUPERNOVA.EBV,
            str(row['E_B-V_']),
            source,
            e_value=str(row['e_E_B-V_']) if row['e_E_B-V_'] else '')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)

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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if row['f_Name']:
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'Ia',
                                               source)
        if row['z']:
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                str(row['z']),
                source,
                kind='spectroscopic')
        else:
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, str(row['zCl']), source, kind='cluster')
        catalog.entries[name].add_quantity(SUPERNOVA.EBV,
                                           str(row['E_B-V_']), source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)

    result = Vizier.get_catalogs('J/ApJ/746/85/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SCP', 'SCP-')
        flux = row['Flux']
        err = row['e_Flux']
        zp = row['Zero']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJ...746...85S')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filter'],
            PHOTOMETRY.COUNT_RATE: str(flux),
            PHOTOMETRY.E_COUNT_RATE: str(err),
            PHOTOMETRY.ZERO_POINT: str(zp),
            PHOTOMETRY.SOURCE: source,
            PHOTOMETRY.INSTRUMENT: row['Inst']
        }
        set_pd_mag_from_counts(photodict, flux, ec=err, zp=zp)
        catalog.entries[name].add_photometry(**photodict)

    # 2004ApJ...602..571B
    result = Vizier.get_catalogs('J/ApJ/602/571/table8')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SN' + row['SN']
        flux = row['Flux']
        err = row['e_Flux']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2004ApJ...602..571B')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        band = row['Filt']
        bandset = ''
        telescope = ''
        if band in ['R', 'I']:
            bandset = 'Cousins'
        if band == 'Z':
            telescope = 'Subaru'
        zp = 25.0
        photodict = {
            PHOTOMETRY.TIME: str(row['MJD']),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.BAND_SET: bandset,
            PHOTOMETRY.COUNT_RATE: flux,
            PHOTOMETRY.E_COUNT_RATE: err,
            PHOTOMETRY.ZERO_POINT: str(zp),
            PHOTOMETRY.TELESCOPE: telescope,
            PHOTOMETRY.SOURCE: source
        }
        set_pd_mag_from_counts(photodict, flux, ec=err, zp=zp)
        catalog.entries[name].add_photometry(**photodict)

    # 2014MNRAS.444.3258M
    result = Vizier.get_catalogs('J/MNRAS/444/3258/SNe')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    oldname = ''
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        if name == oldname:
            continue
        oldname = name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.444.3258M')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            str(row['z']),
            source,
            kind='heliocentric',
            e_value=str(row['e_z']))
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, str(row['_RA']), source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, str(row['_DE']), source, u_value='floatdegrees')
    catalog.journal_entries()

    # 2014MNRAS.438.1391P
    result = Vizier.get_catalogs('J/MNRAS/438/1391/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014MNRAS.438.1391P')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['zh']), source, kind='heliocentric')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
    catalog.journal_entries()

    # 2012ApJ...749...18B
    result = Vizier.get_catalogs('J/ApJ/749/18/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace(' ', '')
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2012ApJ...749...18B')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        mjd = str(
            astrotime(
                float(Decimal('2450000') + Decimal(row['JD'])), format='jd')
            .mjd)
        band = row['Filt'].upper()
        magnitude = str(row['mag'])
        e_magnitude = str(row['e_mag'])
        e_magnitude = '' if e_magnitude == '--' else e_magnitude
        upperlimit = True if row['l_mag'] == '>' else False
        photodict = {
            PHOTOMETRY.TIME: mjd,
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.MAGNITUDE: magnitude,
            PHOTOMETRY.E_MAGNITUDE: e_magnitude,
            PHOTOMETRY.INSTRUMENT: 'UVOT',
            PHOTOMETRY.SOURCE: source,
            PHOTOMETRY.UPPER_LIMIT: upperlimit,
            PHOTOMETRY.TELESCOPE: 'Swift',
            PHOTOMETRY.SYSTEM: 'Swift'
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2010A&A...523A...7G
    result = Vizier.get_catalogs('J/A+A/523/A7/table9')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SNLS-' + row['SNLS']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010A&A...523A...7G')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        astrot = astrotime(
            float(Decimal('2450000') + Decimal(row['Date1'])),
            format='jd').datetime
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE,
            make_date_string(astrot.year, astrot.month, astrot.day), source)
        catalog.entries[name].add_quantity(SUPERNOVA.EBV,
                                           str(row['E_B-V_']), source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['z']), source, kind='heliocentric')
        type_str = (row['Type'].replace('*', '?').replace('SN', '')
                    .replace('(pec)', ' P').replace('Ia? P?', 'Ia P?'))
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, type_str,
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
    catalog.journal_entries()

    # 2004A&A...415..863G
    result = Vizier.get_catalogs('J/A+A/415/863/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SN' + row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2004A&A...415..863G')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        datesplit = row['Date'].split('-')
        date_str = make_date_string(datesplit[0], datesplit[1].lstrip('0'),
                                    datesplit[2].lstrip('0'))
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, date_str,
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST, 'Abell ' + str(row['Abell']), source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row['Type'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        if row['zSN']:
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                str(row['zSN']),
                source,
                kind='spectroscopic')
        else:
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, str(row['zCl']), source, kind='cluster')
    catalog.journal_entries()

    # 2008AJ....136.2306H
    result = Vizier.get_catalogs('J/AJ/136/2306/sources')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SDSS-II SN ' + str(row['SNID'])
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2008AJ....136.2306H')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE,
            row['SpType'].replace('SN.', '').strip(':'), source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)

    # 2010ApJ...708..661D
    result = Vizier.get_catalogs('J/ApJ/708/661/sn')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        if not name:
            name = 'SDSS-II SN ' + str(row['SDSS-II'])
        else:
            name = 'SN' + name
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010ApJ...708..661D')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.ALIAS, 'SDSS-II SN ' + str(row['SDSS-II']), source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'II P',
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)

    result = Vizier.get_catalogs('J/ApJ/708/661/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        if row['f_SN'] == 'a':
            name = 'SDSS-II ' + str(row['SN'])
        else:
            name = 'SN' + row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2010ApJ...708..661D')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, str(row['z']), source, e_value=str(row['e_z']))
    catalog.journal_entries()

    # 2014ApJ...795...44R
    result = Vizier.get_catalogs('J/ApJ/795/44/ps1_snIa')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...795...44R')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        astrot = astrotime(float(row['tdisc']), format='mjd').datetime
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE,
            make_date_string(astrot.year, astrot.month, astrot.day), source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            str(row['z']),
            source,
            e_value=str(row['e_z']),
            kind='heliocentric')
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, kind='spectroscopic')

    result = Vizier.get_catalogs('J/ApJ/795/44/table6')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['SN']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2014ApJ...795...44R')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        if row['mag'] != '--':
            photodict = {
                PHOTOMETRY.TIME: str(row['MJD']),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: row['Filt'],
                PHOTOMETRY.MAGNITUDE: str(row['mag']),
                PHOTOMETRY.E_MAGNITUDE: str(row['e_mag']),
                PHOTOMETRY.SOURCE: source,
                PHOTOMETRY.SYSTEM: 'AB',
                PHOTOMETRY.TELESCOPE: 'PS1',
                PHOTOMETRY.INSTRUMENT: 'GPC'
            }
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 1990A&AS...82..145C
    result = Vizier.get_catalogs('II/189/mag')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)

    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'II_189_refs.csv')) as f:
        tsvin = csv.reader(f, delimiter='\t', skipinitialspace=True)
        ii189bibdict = {}
        ii189refdict = {}
        for r, row in enumerate(tsvin):
            if row[0] != '0':
                if row[1] in ii189bibdict:
                    ii189bibdict[row[1]].append(str(row[2]))
                else:
                    ii189bibdict[row[1]] = [str(row[2])]
            else:
                rn = str(row[3]).strip('() ').capitalize()
                if row[1] in ii189refdict:
                    ii189refdict[row[1]].append(rn)
                else:
                    ii189refdict[row[1]] = [rn]

    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        if row['band'][0] == '(':
            continue
        oldname = 'SN' + row['SN']
        name = catalog.add_entry(oldname)
        source = ''
        sources = [
            catalog.entries[name].add_source(
                bibcode='1990A&AS...82..145C', secondary=True)
        ]
        mjd = str(jd_to_mjd(Decimal(row['JD'])))
        mag = str(row['m'])
        band = row['band'].strip("'")
        if row['r_m'] in ii189bibdict:
            for bc in ii189bibdict[row['r_m']]:
                sources.append(catalog.entries[name].add_source(bibcode=bc))
        if row['r_m'] in ii189refdict:
            for rn in ii189refdict[row['r_m']]:
                sources.append(catalog.entries[name].add_source(name=rn))
        sources = uniq_cdl(sources)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname, sources)

        photodict = {
            PHOTOMETRY.TIME: mjd,
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: band,
            PHOTOMETRY.MAGNITUDE: mag,
            PHOTOMETRY.SOURCE: sources
        }
        catalog.entries[name].add_photometry(**photodict)
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
        source = (catalog.entries[name].add_source(
            bibcode='2014BASI...42...47G') + ',' +
                  (catalog.entries[name].add_source(
                      name='Galactic SNRs',
                      url=('https://www.mrao.cam.ac.uk/'
                           'surveys/snrs/snrs.data.html'))))
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname, source)

        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row['SNR'].strip(),
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.ALIAS, 'MWSNR ' + row['SNR'].strip('G '), source)

        if row['Names']:
            names = row['Names'].split(',')
            for nam in names:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.ALIAS,
                    nam.replace('Vela (XYZ)', 'Vela').strip('()').strip(),
                    source)
                if nam.strip()[:2] == 'SN':
                    catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                                       nam.strip()[2:], source)

        catalog.entries[name].add_quantity(SUPERNOVA.HOST, 'Milky Way', source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            str(row['zhost']),
            source,
            kind='host')
        catalog.entries[name].add_quantity(SUPERNOVA.EBV,
                                           str(row['E_B-V_']), source)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: row['MJD'],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row['e_' + bandtag],
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.TELESCOPE: instr,
                    PHOTOMETRY.INSTRUMENT: instr
                }
                catalog.entries[name].add_photometry(**photodict)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, 'SN' + row['SN'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST, row['Gal'], source)
        if is_number(row['cz']):
            red_str = str(
                round_sig(
                    float(row['cz']) * KM / CLIGHT,
                    sig=get_sig_digits(str(row['cz']))))
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, red_str, source, kind='heliocentric')
        catalog.entries[name].add_quantity(SUPERNOVA.EBV,
                                           str(row['E_B-V_']), source)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['z'],
            source,
            e_value=row['e_z'],
            kind='heliocentric')
        catalog.entries[name].add_quantity(SUPERNOVA.EBV, row['E_B-V_'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, kind='spectroscopic')
    result = Vizier.get_catalogs('J/ApJS/219/13/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'LSQ' + row['LSQ']
        name = catalog.add_entry(name)
        source = catalog.entries[name].add_source(
            bibcode='2015ApJS..219...13W')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        photodict = {
            PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row['JD']))),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.INSTRUMENT: 'QUEST',
            PHOTOMETRY.OBSERVATORY: 'La Silla',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: 'ESO Schmidt',
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SYSTEM: 'Swope',
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2012Natur.491..228C
    result = Vizier.get_catalogs('J/other/Nat/491.228/tablef1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN2213-1745'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012Natur.491..228C')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'SLSN-R',
                                       source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['g', 'r', 'i']:
            bandtag = band + '_mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: row['MJD' + band + '_'],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band + "'",
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row['e_' + bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/other/Nat/491.228/tablef2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN1000+0216'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012Natur.491..228C')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'SLSN-II?',
                                       source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['g', 'r', 'i']:
            bandtag = band + '_mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: row['MJD' + band + '_'],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band + "'",
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row['e_' + bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2011ApJ...736..159G
    result = Vizier.get_catalogs('J/ApJ/736/159/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PTF10vdl'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...736..159G')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        photodict = {
            PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row['JD']))),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: row['Tel'],
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag']
            if is_number(row['e_mag']) else '',
            PHOTOMETRY.UPPER_LIMIT: (not is_number(row['e_mag'])),
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2012ApJ...760L..33B
    result = Vizier.get_catalogs('J/ApJ/760/L33/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PTF12gzk'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2012ApJ...760L..33B')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        # Fixing a typo in VizieR table
        if str(row['JD']) == '2455151.456':
            row['JD'] = '2456151.456'
        photodict = {
            PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row['JD']))),
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: row['Inst'],
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2013ApJ...769...39S
    result = Vizier.get_catalogs('J/ApJ/769/39/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'PS1-12sk'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013ApJ...769...39S')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        instrument = ''
        telescope = ''
        if row['Inst'] == 'RATCam':
            instrument = row['Inst']
        else:
            telescope = row['Inst']
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: telescope,
            PHOTOMETRY.INSTRUMENT: instrument,
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'] if not row['l_mag'] else '',
            PHOTOMETRY.UPPER_LIMIT: (row['l_mag'] == '>'),
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2009MNRAS.394.2266P
    # Note: Instrument info available via links in VizieR, can't auto-parse
    # just yet.
    name = 'SN2005cs'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2009MNRAS.394.2266P')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    result = Vizier.get_catalogs('J/MNRAS/394/2266/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['U', 'B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                e_mag = (row['e_' + bandtag]
                         if row['l_' + bandtag] != '>' else '')
                upl = row['l_' + bandtag] == '>'
                photodict = {
                    PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row['JD']))),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: e_mag,
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.UPPER_LIMIT: upl
                }
                catalog.entries[name].add_photometry(**photodict)
        if ('zmag' in row and is_number(row['zmag']) and
                not isnan(float(row['zmag']))):
            photodict = {
                PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row['JD']))),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: 'z',
                PHOTOMETRY.MAGNITUDE: row['zmag'],
                PHOTOMETRY.E_MAGNITUDE: row['e_zmag'],
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/MNRAS/394/2266/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                time = str(jd_to_mjd(Decimal(row['JD'])))
                e_mag = (row['e_' + bandtag]
                         if row['l_' + bandtag] != '>' else '')
                catalog.entries[name].add_photometry(
                    time=time,
                    u_time='MJD',
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=e_mag,
                    source=source,
                    upperlimit=(row['l_' + bandtag] == '>'))

    result = Vizier.get_catalogs('J/MNRAS/394/2266/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['J', 'H', 'K']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row['JD']))),
                    u_time='MJD',
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row['e_' + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2013AJ....145...99A
    result = Vizier.get_catalogs('J/AJ/145/99/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    name = 'SN2003ie'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013AJ....145...99A')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'R']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row["MJD"],
                    u_time='MJD',
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag]
                    if not row["l_" + bandtag] else '',
                    upperlimit=(row['l_' + bandtag] == '>'),
                    source=source)
        for band in ['V', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=row["MJD"],
                    u_time='MJD',
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag]
                    if is_number(row["e_" + bandtag]) else '',
                    upperlimit=(not is_number(row["e_" + bandtag])),
                    source=source)
    catalog.journal_entries()

    # 2011ApJ...729..143C
    name = 'SN2008am'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...729..143C')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/ApJ/729/143/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        e_mag = row['e_mag'] if not row['l_mag'] else ''
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: 'ROTSE',
            PHOTOMETRY.TELESCOPE: 'ROTSE',
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: e_mag,
            PHOTOMETRY.UPPER_LIMIT: (row['l_mag'] == '<'),
            PHOTOMETRY.SYSTEM: 'Vega',
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/ApJ/729/143/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['J', 'H', 'Ks']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: row["MJD"],
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.TELESCOPE: "PAIRITEL",
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.SYSTEM: 'Vega',
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/ApJ/729/143/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.TELESCOPE: 'P60',
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SYSTEM: 'AB',
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/ApJ/729/143/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        photodict = {
            PHOTOMETRY.TIME: row['MJD'],
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.INSTRUMENT: 'UVOT',
            PHOTOMETRY.TELESCOPE: 'Swift',
            PHOTOMETRY.MAGNITUDE: row['mag'],
            PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
            PHOTOMETRY.SYSTEM: 'Vega',
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2011ApJ...728...14P
    name = 'SN2009bb'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011ApJ...728...14P')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row["JD"]))),
                    u_time='MJD',
                    telescope=row["Tel"],
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['u', 'g', 'r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=str(jd_to_mjd(Decimal(row["JD"]))),
                    u_time='MJD',
                    telescope=row["Tel"],
                    band=band + "'",
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)

    result = Vizier.get_catalogs('J/ApJ/728/14/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['Y', 'J', 'H']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(row["JD"]))),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.INSTRUMENT: row['Inst'],
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2011PAZh...37..837T
    name = 'SN2009nr'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2011PAZh...37..837T')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/PAZh/37/837/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + Decimal('2455000')))
        for band in ['U', 'B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    telescope=row["Tel"],
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2013MNRAS.433.1871B
    name = 'SN2012aw'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2013MNRAS.433.1871B')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/MNRAS/433/1871/table3a')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + Decimal('2456000')))
        for band in ['U', 'B', 'V', 'Rc', 'Ic']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    telescope=row["Tel"],
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)

    result = Vizier.get_catalogs('J/MNRAS/433/1871/table3b')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = str(jd_to_mjd(Decimal(row['JD']) + Decimal('2456000')))
        for band in ['g', 'r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    telescope=row["Tel"],
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2014AJ....148....1Z
    name = 'SN2012fr'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2014AJ....148....1Z')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/AJ/148/1/table2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.TELESCOPE: "LJT",
                    PHOTOMETRY.INSTRUMENT: "YFOSC",
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/AJ/148/1/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['U', 'B', 'V', 'UVW1', 'UVW2', 'UVM2']:
            bandtag = band + 'mag' if len(band) == 1 else band
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.TELESCOPE: "Swift",
                    PHOTOMETRY.INSTRUMENT: "UVOT",
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)

    result = Vizier.get_catalogs('J/AJ/148/1/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                catalog.entries[name].add_photometry(
                    time=mjd,
                    u_time='MJD',
                    telescope="LJT",
                    band=band,
                    magnitude=row[bandtag],
                    e_magnitude=row["e_" + bandtag],
                    source=source)
    catalog.journal_entries()

    # 2015ApJ...805...74B
    name = 'SN2014J'
    name = catalog.add_entry(name)
    source = catalog.entries[name].add_source(bibcode='2014AJ....148....1Z')
    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

    result = Vizier.get_catalogs('J/ApJ/805/74/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        mjd = row['MJD']
        if ('mag' in row and is_number(row['mag']) and
                not isnan(float(row['mag']))):
            photodict = {
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TELESCOPE: 'Swift',
                PHOTOMETRY.INSTRUMENT: 'UVOT',
                PHOTOMETRY.BAND: row['Filt'],
                PHOTOMETRY.MAGNITUDE: row['mag'],
                PHOTOMETRY.E_MAGNITUDE: row['e_mag'],
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
        elif ('maglim' in row and is_number(row['maglim']) and
              not isnan(float(row['maglim']))):
            photodict = {
                PHOTOMETRY.TIME: mjd,
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TELESCOPE: 'Swift',
                PHOTOMETRY.INSTRUMENT: 'UVOT',
                PHOTOMETRY.BAND: row['Filt'],
                PHOTOMETRY.MAGNITUDE: row['maglim'],
                PHOTOMETRY.UPPER_LIMIT: True,
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_photometry(
            time=str(jd_to_mjd(Decimal(row['JD']))),
            u_time='MJD',
            band=row['Filt'],
            magnitude=row['mag'],
            e_magnitude=row['e_mag'] if is_number(row['e_mag']) else '',
            upperlimit=(not is_number(row['e_mag'])),
            source=source)
    catalog.journal_entries()

    # 2015MNRAS.448.1206M
    # Note: Photometry from two SN can also be added from this source.
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, kind='spectroscopic')
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table4')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['zph'],
            source,
            e_value=row['e_zph'],
            kind='photometric')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia?', source, kind='photometric')
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table5')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, row['Type'], source, kind='spectroscopic')
    result = Vizier.get_catalogs('J/MNRAS/448/1206/table6')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, row['Type'], source, kind='photometric')
    result = Vizier.get_catalogs('J/MNRAS/448/1206/tablea2')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE,
            row['Typesoft'] + '?',
            source,
            kind='photometric')
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE,
            row['Typepsnid'] + '?',
            source,
            kind='photometric')
    result = Vizier.get_catalogs('J/MNRAS/448/1206/tablea3')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        oname = str(row['Name'])
        name, source = catalog.new_entry(oname, bibcode='2015MNRAS.448.1206M')
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + oname[4:6], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_APP_MAG,
            row['rP1mag'],
            source,
            e_value=row['e_rP1mag'])
        catalog.entries[name].add_quantity(SUPERNOVA.MAX_BAND, 'r', source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'Candidate',
                                           source)
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
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                           'Ia-' + row['Wcl'], source)
    catalog.journal_entries()

    # 2015ApJS..220....9F
    excludes = ['SN2009y']
    for viztab in ['1', '2']:
        result = Vizier.get_catalogs('J/ApJS/220/9/table' + viztab)
        table = result[list(result.keys())[0]]
        table.convert_bytestring_to_unicode(python3_only=True)
        for row in pbar(table, task_str):
            row = convert_aq_output(row)
            if row['SN'].lower() in excludes:
                continue
            name = catalog.add_entry(name=row['SN'])
            source = catalog.entries[name].add_source(
                bibcode='2015ApJS..220....9F')
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                               row['Type'], source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
            catalog.entries[name].add_quantity(
                SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
            if '?' not in row['Host']:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.HOST, row['Host'].replace('_', ' '), source)
            kind = ''
            if 'Host' in row['n_z']:
                kind = SUPERNOVA.HOST
            elif 'Spectrum' in row['n_z']:
                kind = 'spectroscopic'
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT,
                row['z'],
                source,
                e_value=row['e_z'],
                kind=kind)

    result = Vizier.get_catalogs('J/ApJS/220/9/table8')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = catalog.add_entry(row['SN'])
        source = catalog.entries[name].add_source(
            bibcode='2015ApJS..220....9F')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row['Type'],
                                           source)
        catalog.entries[name].add_photometry(
            time=row['MJD'],
            u_time='MJD',
            band=row['Band'],
            magnitude=row['mag'],
            e_magnitude=row['e_mag'],
            telescope=row['Tel'],
            source=source)
    catalog.journal_entries()

    result = Vizier.get_catalogs('J/ApJ/673/999/table1')
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = catalog.add_entry(name='SN' + row['SN'])
        source = catalog.entries[name].add_source(
            bibcode='2008ApJ...673..999P')
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['z'],
            source,
            kind='host')
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST_RA, row['RAGdeg'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST_DEC, row['DEGdeg'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                           row['Type'].strip(':'), source)
    catalog.journal_entries()

    # 2011MNRAS.417..916G
    result = Vizier.get_catalogs("J/MNRAS/417/916/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SNSDF' + row['SNSDF'], bibcode="2011MNRAS.417..916G")
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['zsp'] if row['zsp'] else row['zph'],
            source,
            kind='host')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE,
            '20' + row['SNSDF'][:2] + '/' + row['SNSDF'][2:4], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST_OFFSET_ANG,
            row['Offset'],
            source,
            u_value='arcseconds')
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, row['Type'], source, kind='photometric')
    catalog.journal_entries()

    # 2013MNRAS.430.1746G
    result = Vizier.get_catalogs("J/MNRAS/430/1746/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SDSS' + row['SDSS'], bibcode="2013MNRAS.430.1746G")
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DISCOVER_DATE, row['Date'].replace('-', '/'), source)
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['z'],
            source,
            kind='host')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row['Type'],
                                           source)
    catalog.journal_entries()

    # 2014AJ....148...13R
    result = Vizier.get_catalogs("J/AJ/148/13/high_z")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['Name'], bibcode="2014AJ....148...13R")
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + row['Name'][3:5], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['zSN'],
            source,
            kind='heliocentric',
            e_value=row['e_zSN'])
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_RA, row['RAG'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_DEC, row['DEG'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST_OFFSET_ANG,
            row['ASep'],
            source,
            u_value='arcseconds')
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['zhost'],
            source,
            kind='host',
            e_value=row['e_zhost'])
    result = Vizier.get_catalogs("J/AJ/148/13/low_z")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['Name'], bibcode="2014AJ....148...13R")
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                           '20' + row['Name'][3:5], source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['zSN'],
            source,
            kind='heliocentric',
            e_value=row['e_zSN'])
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_RA, row['RAG'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_DEC, row['DEG'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.HOST_OFFSET_ANG,
            row['ASep'],
            source,
            u_value='arcseconds')
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['zhost'],
            source,
            kind='host',
            e_value=row['e_zhost'])
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
        name, source = catalog.new_entry(name, bibcode="2007ApJ...666..674M")
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, essname, source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['zSN'],
            source,
            e_value=row['e_zSN'],
            kind='heliocentric')
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['zGal'],
            source,
            kind='host')
        catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, row['SType']
                                           if row['SType'] else row['Type'],
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
            row['Name'], bibcode="2013AcA....63....1K")
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row['OGLEIV'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        astrot = astrotime(float(row['Tmax']), format='jd').datetime
        catalog.entries[name].add_quantity(
            SUPERNOVA.MAX_DATE,
            make_date_string(astrot.year, astrot.month, astrot.day), source)
    catalog.journal_entries()

    # 2011MNRAS.410.1262W
    result = Vizier.get_catalogs("J/MNRAS/410/1262/tablea2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            'SNLS-' + row['SN'], bibcode="2011MNRAS.410.1262W")
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['_RA'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['_DE'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['z'],
            source,
            e_value=row['e_z'],
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
        name, source = catalog.new_entry(name, bibcode="2012ApJ...755...61S")
        err = row['e_z'] if is_number(row['e_z']) else ''
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, sdssname, source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['z'],
            source,
            e_value=err,
            kind='host')
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
        name, source = catalog.new_entry(name, bibcode="2008AJ....135..348S")
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, sdssname, source)
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal('360') + fra
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, str(fra), source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['zsp'], source, kind='spectroscopic')
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, row['Type'].replace('SN', '').strip(),
            source)
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
        name, source = catalog.new_entry(name, bibcode="2010ApJ...713.1026D")
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, sdssname, source)
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, row['RAJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['z'], source, kind='heliocentric')
    catalog.journal_entries()

    # 2013ApJ...770..107C
    result = Vizier.get_catalogs("J/ApJ/770/107/galaxies")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name, source = catalog.new_entry(
            row['SN'], bibcode="2013ApJ...770..107C")
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST_DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(
            [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
            row['z'],
            source,
            e_value=row['e_z'] if is_number(row['e_z']) else '',
            kind='host')
    catalog.journal_entries()

    # 2011ApJ...738..162S
    result = Vizier.get_catalogs("J/ApJ/738/162/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SDSS-II SN ' + row['CID']
        name, source = catalog.new_entry(name, bibcode="2011ApJ...738..162S")
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal('360') + fra
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, str(fra), source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT,
            row['z'],
            source,
            kind='spectroscopic',
            e_value=row['e_z'])
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, probability=row['PzIa'])
    result = Vizier.get_catalogs("J/ApJ/738/162/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = 'SDSS-II SN ' + row['CID']
        name, source = catalog.new_entry(name, bibcode="2011ApJ...738..162S")
        fra = Decimal(row['RAJ2000'])
        if fra < Decimal(0.0):
            fra = Decimal('360') + fra
        catalog.entries[name].add_quantity(
            SUPERNOVA.RA, str(fra), source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.DEC, row['DEJ2000'], source, u_value='floatdegrees')
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['zph'], source, kind='photometric')
        catalog.entries[name].add_quantity(
            SUPERNOVA.CLAIMED_TYPE, 'Ia', source, probability=row['PIa'])
    catalog.journal_entries()

    # 2015MNRAS.446..943V
    snrtabs = [
        "ngc2403", "ngc2903", "ngc300", "ngc3077", "ngc4214", "ngc4395",
        "ngc4449", "ngc5204", "ngc5585", "ngc6946", "ngc7793", "m33", "m74",
        "m81", "m82", "m83", "m101", "m31"
    ]
    for tab in pbar(snrtabs, task_str):
        result = Vizier.get_catalogs("J/MNRAS/446/943/" + tab)
        table = result[list(result.keys())[0]]
        table.convert_bytestring_to_unicode(python3_only=True)
        for ri, row in enumerate(pbar(table, task_str)):
            row = convert_aq_output(row)
            ra = (row['RAJ2000']
                  if isinstance(row['RAJ2000'], str) else radec_clean(
                      str(row['RAJ2000']), SUPERNOVA.RA,
                      unit='floatdegrees')[0])
            dec = (row['DEJ2000']
                   if isinstance(row['DEJ2000'], str) else radec_clean(
                       str(row['DEJ2000']), SUPERNOVA.DEC,
                       unit='floatdegrees')[0])
            name = (tab.upper() + 'SNR J' + rep_chars(ra, ' :.') + rep_chars(
                dec, ' :.'))
            name, source = catalog.new_entry(
                name, bibcode="2015MNRAS.446..943V")
            catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec, source)
            catalog.entries[name].add_quantity(SUPERNOVA.HOST,
                                               tab.upper(), source)
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
        name, source = catalog.new_entry(name, bibcode="2009ApJ...703..370C")
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.HOST, row['Gal'], source)
    catalog.journal_entries()

    # 2016ApJ...821...57D
    name, source = catalog.new_entry('SN2013ge', bibcode="2016ApJ...821...57D")
    result = Vizier.get_catalogs("J/ApJ/821/57/table1")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['UVW2', 'UVM2', 'UVW1', 'U', 'B', 'V']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row["MJD"]),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.TELESCOPE: 'Swift',
                    PHOTOMETRY.INSTRUMENT: 'UVOT',
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
    result = Vizier.get_catalogs("J/ApJ/821/57/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', 'R', 'I']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row["MJD"]),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.INSTRUMENT: 'CAO',
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
    result = Vizier.get_catalogs("J/ApJ/821/57/table3")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['B', 'V', "r'", "i'"]:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                photodict = {
                    PHOTOMETRY.TIME: str(row["MJD"]),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.E_MAGNITUDE: row["e_" + bandtag],
                    PHOTOMETRY.INSTRUMENT: 'FLWO',
                    PHOTOMETRY.SOURCE: source
                }
                catalog.entries[name].add_photometry(**photodict)
    result = Vizier.get_catalogs("J/ApJ/821/57/table4")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        for band in ['r', 'i', 'z']:
            bandtag = band + 'mag'
            if (bandtag in row and is_number(row[bandtag]) and
                    not isnan(float(row[bandtag]))):
                upp = False
                if "l_" + bandtag in row and row["l_" + bandtag] == ">":
                    upp = True
                e_mag = row["e_" + bandtag] if is_number(row["e_" +
                                                             bandtag]) else ''
                photodict = {
                    PHOTOMETRY.TIME: str(row["MJD"]),
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.MAGNITUDE: row[bandtag],
                    PHOTOMETRY.UPPER_LIMIT: upp,
                    PHOTOMETRY.INSTRUMENT: row["Inst"],
                    PHOTOMETRY.SOURCE: source
                }
                if e_mag:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = e_mag
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    # 2004ApJ...607..665R
    result = Vizier.get_catalogs("J/ApJ/607/665/table1")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(name, bibcode="2004ApJ...607..665R")
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row['OName'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                           source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                           source)
    result = Vizier.get_catalogs("J/ApJ/607/665/table2")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(name, bibcode="2004ApJ...607..665R")
        mjd = str(jd_to_mjd(Decimal('2000') + Decimal(row['HJD'])))
        photodict = {
            PHOTOMETRY.TIME: mjd,
            PHOTOMETRY.U_TIME: 'MJD',
            PHOTOMETRY.BAND: row['Filt'],
            PHOTOMETRY.MAGNITUDE: row['Vega'],
            PHOTOMETRY.SYSTEM: 'Vega',
            PHOTOMETRY.E_MAGNITUDE: row['e_Vega'],
            PHOTOMETRY.SOURCE: source
        }
        catalog.entries[name].add_photometry(**photodict)
    result = Vizier.get_catalogs("J/ApJ/607/665/table5")
    table = result[list(result.keys())[0]]
    table.convert_bytestring_to_unicode(python3_only=True)
    for row in pbar(table, task_str):
        row = convert_aq_output(row)
        name = row['Name'].replace('SN ', 'SN')
        name, source = catalog.new_entry(name, bibcode="2004ApJ...607..665R")
        catalog.entries[name].add_quantity(
            SUPERNOVA.REDSHIFT, row['z'], source, kind='spectroscopic')
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
    for ri, row in enumerate(pbar(table, task_str)):
        row = convert_aq_output(row)
        name = 'SN' + row['SN']
        name = catalog.add_entry(name)

        source = catalog.entries[name].add_source(bibcode=bibcode)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

        if row['RAJ2000']:
            catalog.entries[name].add_quantity(SUPERNOVA.RA, row['RAJ2000'],
                                               source)
        if row['DEJ2000']:
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, row['DEJ2000'],
                                               source)
        if row['RAG']:
            catalog.entries[name].add_quantity(SUPERNOVA.HOST_RA, row['RAG'],
                                               source)
        if row['DEG']:
            catalog.entries[name].add_quantity(SUPERNOVA.HOST_DEC, row['DEG'],
                                               source)
        if row['Gal']:
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, row['Gal'],
                                               source)
        if row['Type']:
            claimedtypes = list(
                set([x.strip(' -') for x in row['Type'].split('|')]))
            for claimedtype in claimedtypes:
                catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                   claimedtype, source)
        if row['z'] and is_number(row['z']):
            if name not in ['SN1985D', 'SN2004cq']:
                catalog.entries[name].add_quantity(
                    [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                    row['z'],
                    source,
                    kind='host')
        if row['Dist'] and is_number(row['Dist']):
            quantdict = {
                QUANTITY.VALUE: row['Dist'],
                QUANTITY.SOURCE: source,
                QUANTITY.KIND: 'host'
            }
            if row['e_Dist'] and is_number(row['e_Dist']):
                quantdict[QUANTITY.E_VALUE] = row['e_Dist']
            catalog.entries[name].add_quantity(SUPERNOVA.LUM_DIST, **quantdict)

        if row['Ddate']:
            datestring = row['Ddate'].replace('-', '/')

            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                               datestring, source)

            if 'photometry' not in catalog.entries[name]:
                if ('Dmag' in row and is_number(row['Dmag']) and
                        not isnan(float(row['Dmag']))):
                    datesplit = row['Ddate'].strip().split('-')
                    if len(datesplit) == 3:
                        datestr = row['Ddate'].strip()
                    elif len(datesplit) == 2:
                        datestr = row['Ddate'].strip() + '-01'
                    elif len(datesplit) == 1:
                        datestr = row['Ddate'].strip() + '-01-01'
                    mjd = str(astrotime(datestr).mjd)
                    catalog.entries[name].add_photometry(
                        time=mjd,
                        u_time='MJD',
                        band=row['Dband'],
                        magnitude=row['Dmag'],
                        source=source)
        if row['Mdate']:
            datestring = row['Mdate'].replace('-', '/')

            catalog.entries[name].add_quantity(SUPERNOVA.MAX_DATE, datestring,
                                               source)

            if 'photometry' not in catalog.entries[name]:
                if ('MMag' in row and is_number(row['MMag']) and
                        not isnan(float(row['MMag']))):
                    datesplit = row['Mdate'].strip().split('-')
                    if len(datesplit) == 3:
                        datestr = row['Mdate'].strip()
                    elif len(datesplit) == 2:
                        datestr = row['Mdate'].strip() + '-01'
                    elif len(datesplit) == 1:
                        datestr = row['Mdate'].strip() + '-01-01'
                    mjd = str(astrotime(datestr).mjd)
                    catalog.entries[name].add_photometry(
                        time=mjd,
                        u_time='MJD',
                        band=row['Mband'],
                        magnitude=row['Mmag'],
                        source=source)

        if catalog.args.travis and ri >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return

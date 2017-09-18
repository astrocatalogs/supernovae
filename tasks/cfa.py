"""Import tasks for the Harvard Center for Astrophysics."""
import csv
import os
from glob import glob
from math import floor

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import (is_number, jd_to_mjd, pbar, pbar_strings,
                                     uniq_cdl)
from astropy.time import Time as astrotime

from decimal import Decimal

from ..supernova import SUPERNOVA
from ..utils import clean_snname

ACKN_CFA = ("This research has made use of the CfA Supernova Archive, "
            "which is funded in part by the National Science Foundation "
            "through grant AST 0907903.")


def do_cfa_photo(catalog):
    """Import photometry from the CfA archive."""
    from html import unescape
    import re
    task_str = catalog.get_current_task_str()
    file_names = glob(
        os.path.join(catalog.get_current_task_repo(), 'cfa-input/*.dat'))
    for fname in pbar_strings(file_names, task_str):
        f = open(fname, 'r')
        tsvin = csv.reader(f, delimiter=' ', skipinitialspace=True)
        csv_data = []
        for r, row in enumerate(tsvin):
            new = []
            for item in row:
                new.extend(item.split('\t'))
            csv_data.append(new)

        for r, row in enumerate(csv_data):
            for c, col in enumerate(row):
                csv_data[r][c] = col.strip()
            csv_data[r] = [_f for _f in csv_data[r] if _f]

        eventname = os.path.basename(os.path.splitext(fname)[0])

        eventparts = eventname.split('_')

        name = clean_snname(eventparts[0])
        name = catalog.add_entry(name)
        secondaryname = 'CfA Supernova Archive'
        secondaryurl = 'https://www.cfa.harvard.edu/supernova/SNarchive.html'
        secondarysource = catalog.entries[name].add_source(
            name=secondaryname,
            url=secondaryurl,
            secondary=True,
            acknowledgment=ACKN_CFA)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name,
                                           secondarysource)

        year = re.findall(r'\d+', name)[0]
        catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, year,
                                           secondarysource)

        eventbands = list(eventparts[1])

        tu = 'MJD'
        jdoffset = Decimal(0.)
        for rc, row in enumerate(csv_data):
            if len(row) > 0 and row[0][0] == "#":
                if len(row[0]) > 2 and row[0][:3] == '#JD':
                    tu = 'JD'
                    rowparts = row[0].split('-')
                    jdoffset = Decimal(rowparts[1])
                elif len(row[0]) > 6 and row[0][:7] == '#Julian':
                    tu = 'JD'
                    jdoffset = Decimal(0.)
                elif len(row) > 1 and row[1].lower() == 'photometry':
                    for ci, col in enumerate(row[2:]):
                        if col[0] == "(":
                            refstr = ' '.join(row[2 + ci:])
                            refstr = refstr.replace('(', '').replace(')', '')
                            bibcode = unescape(refstr)
                            source = catalog.entries[name].add_source(
                                bibcode=bibcode)
                elif len(row) > 1 and row[1] == 'HJD':
                    tu = 'HJD'
                continue

            elif len(row) > 0:
                mjd = row[0]
                for v, val in enumerate(row):
                    if v == 0:
                        if tu == 'JD':
                            mjd = str(jd_to_mjd(Decimal(val) + jdoffset))
                            tuout = 'MJD'
                        elif tu == 'HJD':
                            mjd = str(jd_to_mjd(Decimal(val)))
                            tuout = 'MJD'
                        else:
                            mjd = val
                            tuout = tu
                    elif v % 2 != 0:
                        if float(row[v]) < 90.0:
                            src = secondarysource + ',' + source
                            photodict = {
                                PHOTOMETRY.U_TIME: tuout,
                                PHOTOMETRY.TIME: mjd,
                                PHOTOMETRY.BAND_SET: 'Standard',
                                PHOTOMETRY.BAND: eventbands[(v - 1) // 2],
                                PHOTOMETRY.MAGNITUDE: row[v],
                                PHOTOMETRY.E_MAGNITUDE: row[v + 1],
                                PHOTOMETRY.SOURCE: src
                            }
                            catalog.entries[name].add_photometry(**photodict)
        f.close()

    # Hicken 2012
    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'hicken-2012-standard.dat'), 'r') as infile:
        tsvin = list(csv.reader(infile, delimiter='|', skipinitialspace=True))
        for r, row in enumerate(pbar(tsvin, task_str)):
            if r <= 47:
                continue

            if row[0][:2] != 'sn':
                name = 'SN' + row[0].strip()
            else:
                name = row[0].strip()

            name = catalog.add_entry(name)

            source = catalog.entries[name].add_source(
                bibcode='2012ApJS..200...12H')
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'Ia',
                                               source)
            photodict = {
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TIME: row[2].strip(),
                PHOTOMETRY.BAND: row[1].strip(),
                PHOTOMETRY.BAND_SET: 'Standard',
                PHOTOMETRY.MAGNITUDE: row[6].strip(),
                PHOTOMETRY.E_MAGNITUDE: row[7].strip(),
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)

    # Bianco 2014
    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'bianco-2014-standard.dat'), 'r') as infile:
        tsvin = list(csv.reader(infile, delimiter=' ', skipinitialspace=True))
        for row in pbar(tsvin, task_str):
            name = 'SN' + row[0]
            name = catalog.add_entry(name)

            source = catalog.entries[name].add_source(
                bibcode='2014ApJS..213...19B')
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            photodict = {
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TIME: row[2],
                PHOTOMETRY.BAND: row[1],
                PHOTOMETRY.MAGNITUDE: row[3],
                PHOTOMETRY.E_MAGNITUDE: row[4],
                PHOTOMETRY.TELESCOPE: row[5],
                PHOTOMETRY.BAND_SET: 'Standard',
                PHOTOMETRY.SOURCE: source
            }
            catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return


def do_cfa_spectra(catalog):
    """Import spectra from the CfA archive."""
    task_str = catalog.get_current_task_str()
    # II spectra
    oldname = ''
    file_names = next(
        os.walk(os.path.join(catalog.get_current_task_repo(), 'CfA_SNII')))[1]
    for ni, name in enumerate(pbar_strings(file_names, task_str)):
        fullpath = os.path.join(catalog.get_current_task_repo(),
                                'CfA_SNII/') + name
        origname = name
        if name.startswith('sn') and is_number(name[2:6]):
            name = 'SN' + name[2:]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        reference = 'CfA Supernova Archive'
        refurl = 'https://www.cfa.harvard.edu/supernova/SNarchive.html'
        source = catalog.entries[name].add_source(
            name=reference,
            url=refurl,
            secondary=True,
            acknowledgment=ACKN_CFA)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for fi, fname in enumerate(
                sorted(
                    glob(fullpath + '/*'), key=lambda s: s.lower())):
            filename = os.path.basename(fname)
            fileparts = filename.split('-')
            if origname.startswith('sn') and is_number(origname[2:6]):
                year = fileparts[1][:4]
                month = fileparts[1][4:6]
                day = fileparts[1][6:]
                instrument = fileparts[2].split('.')[0]
            else:
                year = fileparts[2][:4]
                month = fileparts[2][4:6]
                day = fileparts[2][6:]
                instrument = fileparts[3].split('.')[0]
            time = str(
                astrotime(year + '-' + month + '-' + str(floor(float(day)))
                          .zfill(2)).mjd + float(day) - floor(float(day)))
            f = open(fname, 'r')
            data = csv.reader(f, delimiter=' ', skipinitialspace=True)
            data = [list(i) for i in zip(*data)]
            wavelengths = data[0]
            fluxes = data[1]
            errors = data[2]
            sources = uniq_cdl([
                source,
                (catalog.entries[name]
                 .add_source(bibcode='2017arXiv170601030H'))
            ])
            catalog.entries[name].add_spectrum(
                u_wavelengths='Angstrom',
                u_fluxes='erg/s/cm^2/Angstrom',
                filename=filename,
                wavelengths=wavelengths,
                fluxes=fluxes,
                u_time='MJD' if time else '',
                time=time,
                instrument=instrument,
                u_errors='ergs/s/cm^2/Angstrom',
                errors=errors,
                source=sources,
                dereddened=False,
                deredshifted=False)
        if catalog.args.travis and ni >= catalog.TRAVIS_QUERY_LIMIT:
            break
    catalog.journal_entries()

    # Ia spectra
    oldname = ''
    file_names = next(
        os.walk(os.path.join(catalog.get_current_task_repo(), 'CfA_SNIa')))[1]
    for ni, name in enumerate(pbar_strings(file_names, task_str)):
        fullpath = os.path.join(catalog.get_current_task_repo(),
                                'CfA_SNIa/') + name
        origname = name
        if name.startswith('sn') and is_number(name[2:6]):
            name = 'SN' + name[2:]
        if name.startswith('snf') and is_number(name[3:7]):
            name = 'SNF' + name[3:]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        reference = 'CfA Supernova Archive'
        refurl = 'https://www.cfa.harvard.edu/supernova/SNarchive.html'
        source = catalog.entries[name].add_source(
            name=reference,
            url=refurl,
            secondary=True,
            acknowledgment=ACKN_CFA)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for fi, fname in enumerate(
                sorted(
                    glob(fullpath + '/*'), key=lambda s: s.lower())):
            filename = os.path.basename(fname)
            fileparts = filename.split('-')
            if origname.startswith('sn') and is_number(origname[2:6]):
                year = fileparts[1][:4]
                month = fileparts[1][4:6]
                day = fileparts[1][6:]
                instrument = fileparts[2].split('.')[0]
            else:
                year = fileparts[2][:4]
                month = fileparts[2][4:6]
                day = fileparts[2][6:]
                instrument = fileparts[3].split('.')[0]
            time = str(
                astrotime(year + '-' + month + '-' + str(floor(float(day)))
                          .zfill(2)).mjd + float(day) - floor(float(day)))
            f = open(fname, 'r')
            data = csv.reader(f, delimiter=' ', skipinitialspace=True)
            data = [list(i) for i in zip(*data)]
            wavelengths = data[0]
            fluxes = data[1]
            errors = data[2]
            sources = uniq_cdl([
                source, (catalog.entries[name]
                         .add_source(bibcode='2012AJ....143..126B')),
                (catalog.entries[name]
                 .add_source(bibcode='2008AJ....135.1598M'))
            ])
            catalog.entries[name].add_spectrum(
                u_wavelengths='Angstrom',
                u_fluxes='erg/s/cm^2/Angstrom',
                filename=filename,
                wavelengths=wavelengths,
                fluxes=fluxes,
                u_time='MJD' if time else '',
                time=time,
                instrument=instrument,
                u_errors='ergs/s/cm^2/Angstrom',
                errors=errors,
                source=sources,
                dereddened=False,
                deredshifted=False)
        if catalog.args.travis and ni >= catalog.TRAVIS_QUERY_LIMIT:
            break
    catalog.journal_entries()

    # Ibc spectra
    oldname = ''
    file_names = next(
        os.walk(os.path.join(catalog.get_current_task_repo(), 'CfA_SNIbc')))[1]
    for ni, name in enumerate(pbar(file_names, task_str)):
        fullpath = os.path.join(catalog.get_current_task_repo(),
                                'CfA_SNIbc/') + name
        if name.startswith('sn') and is_number(name[2:6]):
            name = 'SN' + name[2:]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        reference = 'CfA Supernova Archive'
        refurl = 'https://www.cfa.harvard.edu/supernova/SNarchive.html'
        source = catalog.entries[name].add_source(
            name=reference,
            url=refurl,
            secondary=True,
            acknowledgment=ACKN_CFA)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for fi, fname in enumerate(
                sorted(
                    glob(fullpath + '/*'), key=lambda s: s.lower())):
            filename = os.path.basename(fname)
            fileparts = filename.split('-')
            instrument = ''
            year = fileparts[1][:4]
            month = fileparts[1][4:6]
            day = fileparts[1][6:].split('.')[0]
            if len(fileparts) > 2:
                instrument = fileparts[-1].split('.')[0]
            time = str(
                astrotime(year + '-' + month + '-' + str(floor(float(day)))
                          .zfill(2)).mjd + float(day) - floor(float(day)))
            f = open(fname, 'r')
            data = csv.reader(f, delimiter=' ', skipinitialspace=True)
            data = [list(i) for i in zip(*data)]
            wavelengths = data[0]
            fluxes = data[1]
            sources = uniq_cdl([
                source, catalog.entries[name]
                .add_source(bibcode='2014AJ....147...99M')
            ])
            catalog.entries[name].add_spectrum(
                u_wavelengths='Angstrom',
                u_fluxes='erg/s/cm^2/Angstrom',
                wavelengths=wavelengths,
                filename=filename,
                fluxes=fluxes,
                u_time='MJD' if time else '',
                time=time,
                instrument=instrument,
                source=sources,
                dereddened=False,
                deredshifted=False)
        if catalog.args.travis and ni >= catalog.TRAVIS_QUERY_LIMIT:
            break
    catalog.journal_entries()

    # Other spectra
    oldname = ''
    file_names = next(
        os.walk(os.path.join(catalog.get_current_task_repo(), 'CfA_Extra')))[1]
    for ni, name in enumerate(pbar_strings(file_names, task_str)):
        fullpath = os.path.join(catalog.get_current_task_repo(),
                                'CfA_Extra/') + name
        if name.startswith('sn') and is_number(name[2:6]):
            name = 'SN' + name[2:]
        name = catalog.get_preferred_name(name)
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)
        reference = 'CfA Supernova Archive'
        refurl = 'https://www.cfa.harvard.edu/supernova/SNarchive.html'
        source = catalog.entries[name].add_source(
            name=reference,
            url=refurl,
            secondary=True,
            acknowledgment=ACKN_CFA)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
        for fi, fname in enumerate(
                sorted(
                    glob(fullpath + '/*'), key=lambda s: s.lower())):
            if not os.path.isfile(fname):
                continue
            filename = os.path.basename(fname)
            if ((not filename.startswith('sn') or
                 not filename.endswith('flm') or any(
                     x in filename
                     for x in ['-interp', '-z', '-dered', '-obj', '-gal']))):
                continue
            fileparts = filename.split('.')[0].split('-')
            instrument = ''
            time = ''
            if len(fileparts) > 1:
                year = fileparts[1][:4]
                month = fileparts[1][4:6]
                day = fileparts[1][6:]
                if is_number(year) and is_number(month) and is_number(day):
                    if len(fileparts) > 2:
                        instrument = fileparts[-1]
                    time = str(
                        astrotime(year + '-' + month + '-' + str(
                            floor(float(day))).zfill(2)).mjd + float(day) -
                        floor(float(day)))
            f = open(fname, 'r')
            data = csv.reader(f, delimiter=' ', skipinitialspace=True)
            data = [list(i) for i in zip(*data)]
            wavelengths = data[0]
            fluxes = [str(Decimal(x) * Decimal(1.0e-15)) for x in data[1]]
            catalog.entries[name].add_spectrum(
                u_wavelengths='Angstrom',
                u_fluxes='erg/s/cm^2/Angstrom',
                wavelengths=wavelengths,
                filename=filename,
                fluxes=fluxes,
                u_time='MJD' if time else '',
                time=time,
                instrument=instrument,
                source=source,
                dereddened=False,
                deredshifted=False)
        if catalog.args.travis and ni >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return

"""Import tasks for Alex Fillipenko's UC Berkeley group.
"""
import csv
import json
import os
import urllib
from math import floor

from astropy.time import Time as astrotime

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import (get_sig_digits, is_number, pbar,
                                     pretty_num, uniq_cdl)

from ..supernova import SUPERNOVA


def do_ucb_photo(catalog):
    task_str = catalog.get_current_task_str()
    sec_ref = 'UCB Filippenko Group\'s Supernova Database (SNDB)'
    sec_refurl = 'http://heracles.astro.berkeley.edu/sndb/info'
    sec_refbib = '2012MNRAS.425.1789S'

    jsontxt = catalog.load_url(
        'http://heracles.astro.berkeley.edu/sndb/download?id=allpubphot',
        os.path.join(catalog.get_current_task_repo(), 'SNDB/allpubphot.json'),
        json_sort='PhotID')
    if not jsontxt:
        return

    photom = json.loads(jsontxt)
    photom = sorted(photom, key=lambda kk: kk['PhotID'])
    for phot in pbar(photom, task_str):
        oldname = phot['ObjName']
        name = catalog.add_entry(oldname)

        sec_source = catalog.entries[name].add_source(
            name=sec_ref, url=sec_refurl, bibcode=sec_refbib, secondary=True)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname,
                                           sec_source)
        if phot['AltObjName']:
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS,
                                               phot['AltObjName'], sec_source)
        sources = [sec_source]
        if phot['Reference']:
            sources += [catalog.entries[name]
                        .add_source(bibcode=phot['Reference'])]
        sources = uniq_cdl(sources)

        if phot['Type'] and phot['Type'].strip() != 'NoMatch':
            for ct in phot['Type'].strip().split(','):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.CLAIMED_TYPE, ct.replace('-norm', '').strip(),
                    sources)
        if phot['DiscDate']:
            catalog.entries[name].add_quantity(
                SUPERNOVA.DISCOVER_DATE, phot['DiscDate'].replace('-', '/'),
                sources)
        if phot['HostName']:
            host = urllib.parse.unquote(phot['HostName']).replace('*', '')
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, host, sources)
        filename = phot['Filename'] if phot['Filename'] else ''

        if not filename:
            raise ValueError('Filename not found for SNDB phot!')
        if not phot['PhotID']:
            raise ValueError('ID not found for SNDB phot!')

        filepath = os.path.join(catalog.get_current_task_repo(),
                                'SNDB/') + filename
        phottxt = catalog.load_url('http://heracles.astro.berkeley.edu/sndb/'
                                   'download?id=dp:' + str(phot['PhotID']),
                                   filepath)

        tsvin = csv.reader(
            phottxt.splitlines(), delimiter=' ', skipinitialspace=True)

        for rr, row in enumerate(tsvin):
            if not len(row) > 0 or row[0] == "#":
                continue
            if 'DOCTYPE' in ''.join(row):
                break
            photodict = {
                PHOTOMETRY.TIME: row[0],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.TELESCOPE: row[5],
                PHOTOMETRY.BAND: row[4],
                PHOTOMETRY.SOURCE: sources
            }
            if is_number(row[1]) and float(row[1]) < 99.0:
                photodict[PHOTOMETRY.MAGNITUDE] = row[1]
                photodict[PHOTOMETRY.E_MAGNITUDE] = row[2]
            elif is_number(row[3]) and float(row[1]) < 99.0:
                photodict[PHOTOMETRY.MAGNITUDE] = row[3]
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            else:
                continue
            catalog.entries[name].add_photometry(**photodict)

    catalog.journal_entries()
    return


def do_ucb_spectra(catalog):
    task_str = catalog.get_current_task_str()
    sec_reference = 'UCB Filippenko Group\'s Supernova Database (SNDB)'
    sec_refurl = 'http://heracles.astro.berkeley.edu/sndb/info'
    sec_refbib = '2012MNRAS.425.1789S'
    ucbspectracnt = 0

    jsontxt = catalog.load_url(
        'http://heracles.astro.berkeley.edu/sndb/download?id=allpubspec',
        os.path.join(catalog.get_current_task_repo(), 'UCB/allpubspec.json'),
        json_sort='SpecID')
    if not jsontxt:
        return

    spectra = json.loads(jsontxt)
    spectra = sorted(spectra, key=lambda kk: kk['SpecID'])
    oldname = ''
    for spectrum in pbar(spectra, task_str):
        name = spectrum['ObjName']
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)

        sec_source = catalog.entries[name].add_source(
            name=sec_reference,
            url=sec_refurl,
            bibcode=sec_refbib,
            secondary=True)
        catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, sec_source)
        sources = [sec_source]
        if spectrum['Reference']:
            sources += [catalog.entries[name]
                        .add_source(bibcode=spectrum['Reference'])]
        sources = uniq_cdl(sources)

        if spectrum['Type'] and spectrum['Type'].strip() != 'NoMatch':
            for ct in spectrum['Type'].strip().split(','):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.CLAIMED_TYPE, ct.replace('-norm', '').strip(),
                    sources)
        if spectrum['DiscDate']:
            ddate = spectrum['DiscDate'].replace('-', '/')
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, ddate,
                                               sources)
        if spectrum['HostName']:
            host = urllib.parse.unquote(spectrum['HostName']).replace('*', '')
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, host, sources)
        if spectrum['UT_Date']:
            epoch = str(spectrum['UT_Date'])
            year = epoch[:4]
            month = epoch[4:6]
            day = epoch[6:]
            sig = get_sig_digits(day) + 5
            mjd = astrotime(year + '-' + month + '-' + str(floor(float(
                day))).zfill(2)).mjd
            mjd = pretty_num(mjd + float(day) - floor(float(day)), sig=sig)
        filename = spectrum['Filename'] if spectrum['Filename'] else ''
        instrument = spectrum['Instrument'] if spectrum['Instrument'] else ''
        reducer = spectrum['Reducer'] if spectrum['Reducer'] else ''
        observer = spectrum['Observer'] if spectrum['Observer'] else ''
        snr = str(spectrum['SNR']) if spectrum['SNR'] else ''

        if not filename:
            raise ValueError('Filename not found for SNDB spectrum!')
        if not spectrum['SpecID']:
            raise ValueError('ID not found for SNDB spectrum!')

        filepath = os.path.join(catalog.get_current_task_repo(),
                                'UCB/') + filename
        spectxt = catalog.load_url(
            'http://heracles.astro.berkeley.edu/sndb/download?id=ds:' +
            str(spectrum['SpecID']),
            filepath,
            archived_mode=True)

        specdata = list(
            csv.reader(
                spectxt.splitlines(), delimiter=' ', skipinitialspace=True))
        newspecdata = []
        for row in specdata:
            if row[0][0] == '#':
                continue
            else:
                newspecdata.append(row)
        specdata = newspecdata

        haserrors = len(specdata[0]) == 3 and specdata[0][2] and specdata[0][
            2] != 'NaN'
        specdata = [list(ii) for ii in zip(*specdata)]

        wavelengths = specdata[0]
        fluxes = specdata[1]
        errors = ''
        if haserrors:
            errors = specdata[2]

        if not list(filter(None, errors)):
            errors = ''

        units = 'Uncalibrated'
        catalog.entries[name].add_spectrum(
            u_wavelengths='Angstrom',
            u_fluxes=units,
            u_time='MJD',
            time=mjd,
            wavelengths=wavelengths,
            filename=filename,
            fluxes=fluxes,
            errors=errors,
            u_errors=units,
            instrument=instrument,
            source=sources,
            snr=snr,
            observer=observer,
            reducer=reducer,
            deredshifted=('-noz' in filename))
        ucbspectracnt = ucbspectracnt + 1
        if catalog.args.travis and ucbspectracnt >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return

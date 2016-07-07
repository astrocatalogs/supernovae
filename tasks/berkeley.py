"""Import tasks for Alex Fillipenko's UC Berkeley group.
"""
import csv
import json
import os
import urllib
from math import floor

import requests
from astropy.time import Time as astrotime

from astrocats.catalog.utils import get_sig_digits, pbar, pretty_num, uniq_cdl


def do_ucb_photo(catalog):
    task_str = catalog.get_current_task_str()
    sec_ref = 'UCB Filippenko Group\'s Supernova Database (SNDB)'
    sec_refurl = 'http://heracles.astro.berkeley.edu/sndb/info'
    sec_refbib = '2012MNRAS.425.1789S'

    jsontxt = catalog.load_cached_url(
        'http://heracles.astro.berkeley.edu/sndb/download?id=allpubphot',
        os.path.join(catalog.get_current_task_repo(), 'SNDB/allpub.json'))
    if not jsontxt:
        return

    photom = json.loads(jsontxt)
    photom = sorted(photom, key=lambda kk: kk['ObjName'])
    for phot in pbar(photom, task_str):
        oldname = phot['ObjName']
        name = catalog.add_entry(oldname)

        sec_source = catalog.entries[name].add_source(
            name=sec_ref, url=sec_refurl,
            bibcode=sec_refbib,
            secondary=True)
        catalog.entries[name].add_quantity('alias', oldname, sec_source)
        sources = [sec_source]
        if phot['Reference']:
            sources += [catalog.entries[name]
                        .add_source(bibcode=phot['Reference'])]
        sources = uniq_cdl(sources)

        if phot['Type'] and phot['Type'].strip() != 'NoMatch':
            for ct in phot['Type'].strip().split(','):
                catalog.entries[name].add_quantity(
                    'claimedtype', ct.replace('-norm', '').strip(), sources)
        if phot['DiscDate']:
            catalog.entries[name].add_quantity(
                'discoverdate', phot['DiscDate'].replace('-', '/'), sources)
        if phot['HostName']:
            host = urllib.parse.unquote(phot['HostName']).replace('*', '')
            catalog.entries[name].add_quantity('host', host, sources)
        filename = phot['Filename'] if phot['Filename'] else ''

        if not filename:
            raise ValueError('Filename not found for SNDB phot!')
        if not phot['PhotID']:
            raise ValueError('ID not found for SNDB phot!')

        filepath = os.path.join(
            catalog.get_current_task_repo(), 'SNDB/') + filename
        if (catalog.current_task.load_archive(catalog.args) and
                os.path.isfile(filepath)):
            with open(filepath, 'r') as ff:
                phottxt = ff.read()
        else:
            session = requests.Session()
            response = session.get(
                'http://heracles.astro.berkeley.edu/sndb/download?id=dp:' +
                str(phot['PhotID']))
            phottxt = response.text
            with open(filepath, 'w') as ff:
                ff.write(phottxt)

        tsvin = csv.reader(phottxt.splitlines(),
                           delimiter=' ', skipinitialspace=True)

        for rr, row in enumerate(tsvin):
            if len(row) > 0 and row[0] == "#":
                continue
            mjd = row[0]
            magnitude = row[1]
            if magnitude and float(magnitude) > 99.0:
                continue
            e_mag = row[2]
            band = row[4]
            telescope = row[5]
            catalog.entries[name].add_photometry(
                time=mjd, telescope=telescope, band=band,
                magnitude=magnitude, e_magnitude=e_mag, source=sources)

    catalog.journal_entries()
    return


def do_ucb_spectra(catalog):
    task_str = catalog.get_current_task_str()
    sec_reference = 'UCB Filippenko Group\'s Supernova Database (SNDB)'
    sec_refurl = 'http://heracles.astro.berkeley.edu/sndb/info'
    sec_refbib = '2012MNRAS.425.1789S'
    ucbspectracnt = 0

    jsontxt = catalog.load_cached_url(
        'http://heracles.astro.berkeley.edu/sndb/download?id=allpubspec',
        os.path.join(catalog.get_current_task_repo(), 'UCB/allpub.json'))
    if not jsontxt:
        return

    spectra = json.loads(jsontxt)
    spectra = sorted(spectra, key=lambda kk: kk['ObjName'])
    oldname = ''
    for spectrum in pbar(spectra, task_str):
        name = spectrum['ObjName']
        if oldname and name != oldname:
            catalog.journal_entries()
        oldname = name
        name = catalog.add_entry(name)

        sec_source = catalog.entries[name].add_source(
            name=sec_reference, url=sec_refurl, bibcode=sec_refbib,
            secondary=True)
        catalog.entries[name].add_quantity('alias', name, sec_source)
        sources = [sec_source]
        if spectrum['Reference']:
            sources += [catalog.entries[name]
                        .add_source(bibcode=spectrum['Reference'])]
        sources = uniq_cdl(sources)

        if spectrum['Type'] and spectrum['Type'].strip() != 'NoMatch':
            for ct in spectrum['Type'].strip().split(','):
                catalog.entries[name].add_quantity(
                    'claimedtype', ct.replace('-norm', '').strip(), sources)
        if spectrum['DiscDate']:
            ddate = spectrum['DiscDate'].replace('-', '/')
            catalog.entries[name].add_quantity('discoverdate', ddate, sources)
        if spectrum['HostName']:
            host = urllib.parse.unquote(spectrum['HostName']).replace('*', '')
            catalog.entries[name].add_quantity('host', host, sources)
        if spectrum['UT_Date']:
            epoch = str(spectrum['UT_Date'])
            year = epoch[:4]
            month = epoch[4:6]
            day = epoch[6:]
            sig = get_sig_digits(day) + 5
            mjd = astrotime(year + '-' + month + '-' +
                            str(floor(float(day))).zfill(2)).mjd
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

        filepath = os.path.join(
            catalog.get_current_task_repo(), 'UCB/') + filename
        if (catalog.current_task.load_archive(catalog.args) and
                os.path.isfile(filepath)):
            with open(filepath, 'r') as ff:
                spectxt = ff.read()
        else:
            session = requests.Session()
            response = session.get(
                'http://heracles.astro.berkeley.edu/sndb/download?id=ds:' +
                str(spectrum['SpecID']))
            spectxt = response.text
            with open(filepath, 'w') as ff:
                ff.write(spectxt)

        specdata = list(csv.reader(spectxt.splitlines(),
                                   delimiter=' ', skipinitialspace=True))
        startrow = 0
        for row in specdata:
            if row[0][0] == '#':
                startrow += 1
            else:
                break
        specdata = specdata[startrow:]

        haserrors = len(specdata[0]) == 3 and specdata[
            0][2] and specdata[0][2] != 'NaN'
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
            'Angstrom', units, u_time='MJD', time=mjd,
            wavelengths=wavelengths, filename=filename, fluxes=fluxes,
            errors=errors,
            errorunit=units, instrument=instrument, source=sources, snr=snr,
            observer=observer,
            reducer=reducer, deredshifted=('-noz' in filename))
        ucbspectracnt = ucbspectracnt + 1
        if catalog.args.travis and ucbspectracnt >= catalog.TRAVIS_QUERY_LIMIT:
            break

    catalog.journal_entries()
    return

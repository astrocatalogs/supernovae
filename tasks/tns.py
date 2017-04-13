"""Import tasks for the Transient Name Server."""
import csv
import json
import os
import time
import urllib
import warnings
from datetime import datetime, timedelta
from math import ceil

import requests

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.spectrum import SPECTRUM
from astrocats.catalog.utils import (is_integer, is_number, jd_to_mjd, pbar,
                                     pretty_num, sortOD)
from decimal import Decimal

from ..supernova import SUPERNOVA


def do_tns(catalog):
    """Load TNS metadata."""
    session = requests.Session()
    task_str = catalog.get_current_task_str()
    tns_url = 'https://wis-tns.weizmann.ac.il/'
    search_url = tns_url + \
        'search?&num_page=1&format=html&sort=desc&order=id&format=csv&page=0'
    csvtxt = catalog.load_url(search_url,
                              os.path.join(catalog.get_current_task_repo(),
                                           'TNS', 'index.csv'))
    if not csvtxt:
        return
    maxid = csvtxt.splitlines()[1].split(',')[0].strip('"')
    maxpages = ceil(int(maxid) / 1000.)

    for page in pbar(range(maxpages), task_str):
        fname = os.path.join(
            catalog.get_current_task_repo(), 'TNS',
            'page-') + str(page).zfill(2) + '.csv'
        if (catalog.current_task.load_archive(catalog.args) and
                os.path.isfile(fname) and page < 7):
            with open(fname, 'r') as tns_file:
                csvtxt = tns_file.read()
        else:
            with open(fname, 'w') as tns_file:
                session = requests.Session()
                ses_url = (tns_url + 'search?&num_page=1000&format=html&edit'
                           '[type]=&edit[objname]=&edit[id]=&sort=asc&order=id'
                           '&display[redshift]=1'
                           '&display[hostname]=1&display[host_redshift]=1'
                           '&display[source_group_name]=1'
                           '&display[programs_name]=1'
                           '&display[internal_name]=1'
                           '&display[isTNS_AT]=1'
                           '&display[public]=1'
                           '&display[end_pop_period]=0'
                           '&display[spectra_count]=1'
                           '&display[discoverymag]=1&display[discmagfilter]=1'
                           '&display[discoverydate]=1&display[discoverer]=1'
                           '&display[sources]=1'
                           '&display[bibcode]=1&format=csv&page=' + str(page))
                try:
                    response = session.get(ses_url)
                    csvtxt = response.text
                except Exception:
                    if os.path.isfile(fname):
                        with open(fname, 'r') as tns_file:
                            csvtxt = tns_file.read()
                    else:
                        continue
                else:
                    tns_file.write(csvtxt)

        tsvin = list(csv.reader(csvtxt.splitlines(), delimiter=','))
        for ri, row in enumerate(pbar(tsvin, task_str, leave=False)):
            if ri == 0:
                continue
            if row[4] and 'SN' not in row[4]:
                continue
            name = row[1].replace(' ', '')
            name = catalog.add_entry(name)
            source = catalog.entries[name].add_source(
                name='Transient Name Server', url=tns_url)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            if row[2] and row[2] != '00:00:00.00':
                catalog.entries[name].add_quantity(SUPERNOVA.RA, row[2],
                                                   source)
            if row[3] and row[3] != '+00:00:00.00':
                catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[3],
                                                   source)
            if row[4]:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.CLAIMED_TYPE, row[4].replace('SN', '').strip(),
                    source)
            if row[5]:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT, row[5], source, kind='spectroscopic')
            if row[6]:
                catalog.entries[name].add_quantity(SUPERNOVA.HOST, row[6],
                                                   source)
            if row[7]:
                catalog.entries[name].add_quantity(
                    [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                    row[7],
                    source,
                    kind='host')
            if row[8]:
                catalog.entries[name].add_quantity(SUPERNOVA.DISCOVERER,
                                                   row[8], source)
            # Currently, all events listing all possible observers. TNS bug?
            # if row[9]:
            #    observers = row[9].split(',')
            #    for observer in observers:
            #        catalog.entries[name].add_quantity('observer',
            #                                  observer.strip(),
            #                                  source)
            if row[10]:
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, row[10],
                                                   source)
            if row[16]:
                date = row[16].split()[0].replace('-', '/')
                if date != '0000/00/00':
                    date = date.replace('/00', '')
                    t = row[16].split()[1]
                    if t != '00:00:00':
                        ts = t.split(':')
                        dt = timedelta(
                            hours=int(ts[0]),
                            minutes=int(ts[1]),
                            seconds=int(ts[2]))
                        date += pretty_num(
                            dt.total_seconds() / (24 * 60 * 60),
                            sig=6).lstrip('0')
                    catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                                       date, source)
            if catalog.args.travis and ri >= catalog.TRAVIS_QUERY_LIMIT:
                break
            if catalog.args.update:
                catalog.journal_entries()

    catalog.journal_entries()


def do_tns_photo(catalog):
    """Load TNS photometry."""
    task_str = catalog.get_current_task_str()
    tns_url = 'https://wis-tns.weizmann.ac.il/'
    try:
        with open('tns.key', 'r') as f:
            tnskey = f.read().splitlines()[0]
    except Exception:
        catalog.log.warning('TNS API key not found, make sure a file named '
                            '`tns.key` containing the key is placed the '
                            'astrocats directory.')
        tnskey = ''

    bandreps = {'Clear': 'C'}
    fails = 0
    for name in pbar(list(catalog.entries.keys()), task_str):
        if name not in catalog.entries:
            continue
        aliases = catalog.entries[name].get_aliases()
        oname = ''
        for alias in aliases:
            if (alias.startswith(('SN', 'AT')) and is_integer(alias[2:6]) and
                    int(alias[2:6]) >= 2016) and alias[6:].isalpha():
                oname = alias
                break
        if not oname:
            continue
        reqname = oname[2:]
        jsonpath = os.path.join(catalog.get_current_task_repo(), 'TNS',
                                reqname + '.json')
        download_json = True
        if os.path.isfile(jsonpath):
            with open(jsonpath, 'r') as f:
                objdict = json.load(f)
            if ('discoverydate' in objdict and
                (datetime.now() - datetime.strptime(objdict['discoverydate'],
                                                    '%Y-%m-%d %H:%M:%S')
                 ).days > 90):
                download_json = False
        if download_json:
            data = urllib.parse.urlencode({
                'api_key': tnskey,
                'data': json.dumps({
                    'objname': reqname,
                    'photometry': '1'
                })
            }).encode('ascii')
            req = urllib.request.Request(
                'https://wis-tns.weizmann.ac.il/api/get/object', data=data)
            trys = 0
            objdict = None
            while trys < 3 and not objdict:
                try:
                    objdict = json.loads(
                        urllib.request.urlopen(req).read().decode('ascii'))[
                            'data']['reply']
                except KeyboardInterrupt:
                    raise
                except Exception:
                    catalog.log.warning('API request failed for `{}`.'.format(
                        name))
                    time.sleep(5)
                trys = trys + 1
            if (not objdict or 'objname' not in objdict or
                    not isinstance(objdict['objname'], str)):
                fails = fails + 1
                catalog.log.warning('Object `{}` not found!'.format(name))
                if fails >= 5:
                    break
                continue
            # Cache object here
            with open(jsonpath, 'w') as f:
                json.dump(sortOD(objdict), f, indent='\t',
                          separators=(',', ':'), ensure_ascii=False,
                          sort_keys=True)

        if 'photometry' not in objdict:
            continue
        photoarr = objdict['photometry']
        name, source = catalog.new_entry(
            oname, srcname='Transient Name Server', url=tns_url)
        for photo in photoarr:
            if 'mag' not in photo['flux_unit']['name'].lower():
                catalog.log.warning('Unknown flux unit `{}`.'.format(photo[
                    'flux_unit']['name']))
                continue
            if not photo['jd']:
                continue
            if not photo['flux'] and not photo['limflux']:
                continue
            mag = photo['flux'] if photo['flux'] else photo['limflux']
            photodict = {
                PHOTOMETRY.TIME: str(jd_to_mjd(Decimal(str(photo['jd'])))),
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.MAGNITUDE: mag,
                PHOTOMETRY.SOURCE: source
            }
            if photo.get('fluxerr', ''):
                photodict[PHOTOMETRY.E_MAGNITUDE] = photo['fluxerr']
            if not photo['flux']:
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            band = photo['filters']['name']
            if band:
                if band in bandreps:
                    band = bandreps[band]
                photodict[PHOTOMETRY.BAND] = band
            if photo.get('observer', ''):
                photodict[PHOTOMETRY.OBSERVER] = photo['observer']
            if 'source_group' in photo:
                survey = photo['source_group']['group_name']
                if survey:
                    photodict[PHOTOMETRY.SURVEY] = survey
            if 'telescope' in photo:
                telescope = photo['telescope']['name']
                if telescope and telescope != 'Other':
                    photodict[PHOTOMETRY.TELESCOPE] = telescope
            if 'instrument' in photo:
                instrument = photo['instrument']['name']
                if instrument and instrument != 'Other':
                    photodict[PHOTOMETRY.INSTRUMENT] = instrument
            system = ''
            if 'Vega' in photo['flux_unit']['name']:
                system = 'Vega'
            elif 'ab' in photo['flux_unit']['name']:
                system = 'AB'
            if system:
                photodict[PHOTOMETRY.SYSTEM] = system
            catalog.entries[name].add_photometry(**photodict)
        catalog.journal_entries()
    return


def do_tns_spectra(catalog):
    """Load TNS spectra."""
    requests.packages.urllib3.disable_warnings()
    task_str = catalog.get_current_task_str()
    tns_url = 'https://wis-tns.weizmann.ac.il/'
    try:
        with open('tns.key', 'r') as f:
            tnskey = f.read().splitlines()[0]
    except Exception:
        catalog.log.warning('TNS API key not found, make sure a file named '
                            '`tns.key` containing the key is placed the '
                            'astrocats directory.')
        tnskey = ''

    fails = 0
    for name in pbar(list(catalog.entries.keys()), task_str):
        if name not in catalog.entries:
            continue
        aliases = catalog.entries[name].get_aliases()
        oname = ''
        for alias in aliases:
            if (alias.startswith(('SN', 'AT')) and is_integer(alias[2:6]) and
                    int(alias[2:6]) >= 2016) and alias[6:].isalpha():
                oname = alias
                break
        if not oname:
            continue
        reqname = oname[2:]
        jsonpath = os.path.join(catalog.get_current_task_repo(), 'TNS', 'meta',
                                reqname + '.json')
        download_json = True
        if os.path.isfile(jsonpath):
            with open(jsonpath, 'r') as f:
                objdict = json.load(f)
            if ('discoverydate' in objdict and
                (datetime.now() - datetime.strptime(objdict['discoverydate'],
                                                    '%Y-%m-%d %H:%M:%S')
                 ).days > 90):
                download_json = False
        if download_json:
            data = urllib.parse.urlencode({
                'api_key': tnskey,
                'data': json.dumps({
                    'objname': reqname,
                    'spectra': '1'
                })
            }).encode('ascii')
            req = urllib.request.Request(
                'https://wis-tns.weizmann.ac.il/api/get/object', data=data)
            trys = 0
            objdict = None
            while trys < 3 and not objdict:
                try:
                    objdict = json.loads(
                        urllib.request.urlopen(req).read().decode('ascii'))[
                            'data']['reply']
                except KeyboardInterrupt:
                    raise
                except Exception:
                    catalog.log.warning('API request failed for `{}`.'.format(
                        name))
                    time.sleep(5)
                trys = trys + 1
            if (not objdict or 'objname' not in objdict or
                    not isinstance(objdict['objname'], str)):
                fails = fails + 1
                catalog.log.warning('Object `{}` not found!'.format(name))
                if fails >= 5:
                    break
                continue
            # Cache object here
            with open(jsonpath, 'w') as f:
                json.dump(sortOD(objdict), f, indent='\t',
                          separators=(',', ':'), ensure_ascii=False,
                          sort_keys=True)

        if 'spectra' not in objdict:
            continue
        specarr = objdict['spectra']
        name, source = catalog.new_entry(
            oname, srcname='Transient Name Server', url=tns_url)
        for spectrum in specarr:
            spectrumdict = {
                PHOTOMETRY.SOURCE: source
            }
            if 'jd' in spectrum:
                spectrumdict[SPECTRUM.TIME] = str(
                    jd_to_mjd(Decimal(str(spectrum['jd']))))
                spectrumdict[SPECTRUM.U_TIME] = 'MJD'
            if spectrum.get('observer', ''):
                spectrumdict[SPECTRUM.OBSERVER] = spectrum['observer']
            if spectrum.get('reducer', ''):
                spectrumdict[SPECTRUM.OBSERVER] = spectrum['observer']
            if 'source_group' in spectrum:
                survey = spectrum['source_group']['name']
                if survey:
                    spectrumdict[SPECTRUM.SURVEY] = survey
            if 'telescope' in spectrum:
                telescope = spectrum['telescope']['name']
                if telescope and telescope != 'Other':
                    spectrumdict[SPECTRUM.TELESCOPE] = telescope
            if 'instrument' in spectrum:
                instrument = spectrum['instrument']['name']
                if instrument and instrument != 'Other':
                    spectrumdict[SPECTRUM.INSTRUMENT] = instrument

            if 'asciifile' in spectrum:
                fname = urllib.parse.unquote(
                    spectrum['asciifile'].split('/')[-1])
                spectxt = catalog.load_url(
                    spectrum['asciifile'],
                    os.path.join(
                        catalog.get_current_task_repo(), 'TNS', 'spectra',
                        fname), archived_mode=True)
                data = [x.split() for x in spectxt.splitlines()]

                skipspec = False
                newdata = []
                oldval = ''
                for row in data:
                    if row and '#' not in row[0]:
                        if (len(row) >= 2 and is_number(row[0]) and
                                is_number(row[1]) and row[1] != oldval):
                            newdata.append(row)
                            oldval = row[1]

                if skipspec or not newdata:
                    warnings.warn('Skipped adding spectrum file ' + fname)
                    continue

                data = [list(i) for i in zip(*newdata)]
                wavelengths = data[0]
                fluxes = data[1]
                errors = ''
                if len(data) == 3:
                    errors = data[1]

                if max([float(x) for x in fluxes]) < 1.0e-5:
                    fluxunit = 'erg/s/cm^2/Angstrom'
                else:
                    fluxunit = 'Uncalibrated'

                spectrumdict.update({
                    SPECTRUM.U_WAVELENGTHS: 'Angstrom',
                    SPECTRUM.ERRORS: errors,
                    SPECTRUM.U_FLUXES: fluxunit,
                    SPECTRUM.U_ERRORS: fluxunit if errors else '',
                    SPECTRUM.WAVELENGTHS: wavelengths,
                    SPECTRUM.FLUXES: fluxes
                })
                catalog.entries[name].add_spectrum(**spectrumdict)
        catalog.journal_entries()
    return

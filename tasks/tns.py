"""Import tasks for the Transient Name Server.
"""
import csv
import json
import os
import time
import urllib
from datetime import timedelta
from math import ceil

import requests
from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import is_integer, jd_to_mjd, pbar, pretty_num

from cdecimal import Decimal

from ..supernova import SUPERNOVA


def do_tns(catalog):
    session = requests.Session()
    task_str = catalog.get_current_task_str()
    tns_url = 'https://wis-tns.weizmann.ac.il/'
    search_url = tns_url + \
        'search?&num_page=1&format=html&sort=desc&order=id&format=csv&page=0'
    csvtxt = catalog.load_url(search_url,
                              os.path.join(catalog.get_current_task_repo(),
                                           'TNS/index.csv'))
    if not csvtxt:
        return
    maxid = csvtxt.splitlines()[1].split(',')[0].strip('"')
    maxpages = ceil(int(maxid) / 1000.)

    for page in pbar(range(maxpages), task_str):
        fname = os.path.join(catalog.get_current_task_repo(), 'TNS/page-') + \
            str(page).zfill(2) + '.csv'
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
                except:
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
                    SUPERNOVA.REDSHIFT, row[7], source, kind='host')
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
    task_str = catalog.get_current_task_str()
    tns_url = 'https://wis-tns.weizmann.ac.il/'
    try:
        with open('tns.key', 'r') as f:
            tnskey = f.read().splitlines()[0]
    except:
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
        data = urllib.parse.urlencode({
            'api_key': tnskey,
            'data': json.dumps({
                'objname': oname[2:],
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
            except:
                catalog.log.warning('API request failed for `{}`.'.format(
                    name))
                time.sleep(5)
            trys = trys + 1
        if not objdict or not isinstance(objdict['objname'], str):
            fails = fails + 1
            catalog.log.warning('Object `{}` not found!'.format(name))
            if fails >= 5:
                break
            continue
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
            if not photo['flux']:
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
            band = photo['filters']['name']
            if band:
                if band in bandreps:
                    band = bandreps[band]
                photodict[PHOTOMETRY.BAND] = band
            if 'observer' in photo:
                if photo['observer']:
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

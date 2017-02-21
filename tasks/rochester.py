"""Import tasks for David Bishop's Latest Supernovae page.
"""
import csv
import os
import re
from math import floor
from string import ascii_letters

from astrocats.catalog.utils import is_number, make_date_string, pbar, uniq_cdl
from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from ..supernova import SUPERNOVA


def do_rochester(catalog):
    rochestermirrors = [
        'http://www.rochesterastronomy.org/',
        'http://www.supernova.thistlethwaites.com/'
    ]
    rochesterpaths = [
        'snimages/snredshiftall.html', 'sn2017/snredshift.html',
        'snimages/snredboneyard.html', 'snimages/snredboneyard-old.html'
    ]
    rochesterupdate = [False, True, True, False]
    task_str = catalog.get_current_task_str()
    baddates = ['2440587', '2440587.292', '0001/01/01']

    for pp, path in enumerate(pbar(rochesterpaths, task_str)):
        if catalog.args.update and not rochesterupdate[pp]:
            continue

        if 'snredboneyard.html' in path:
            cns = {
                'name': 0,
                'host': 1,
                'ra': 2,
                'dec': 3,
                'type': 7,
                'z': 8,
                'mmag': 9,
                'max': 10,
                'disc': 11,
                'ref': 12,
                'dver': 13,
                'aka': 14
            }
        else:
            cns = {
                'name': 0,
                'type': 1,
                'host': 2,
                'ra': 3,
                'dec': 4,
                'disc': 6,
                'max': 7,
                'mmag': 8,
                'z': 11,
                'zh': 12,
                'ref': 13,
                'dver': 14,
                'aka': 15
            }

        filepath = (os.path.join(catalog.get_current_task_repo(), 'rochester/')
                    + path.replace('/', '-'))
        for mirror in rochestermirrors:
            html = catalog.load_url(
                mirror + path, filepath, fail=(mirror != rochestermirrors[-1]))
            if html:
                break

        if not html:
            continue

        soup = BeautifulSoup(html, 'html5lib')
        rows = soup.findAll('tr')
        sec_ref = 'Latest Supernovae'
        sec_refurl = ('http://www.rochesterastronomy.org/'
                      'snimages/snredshiftall.html')
        loopcnt = 0
        for rr, row in enumerate(pbar(rows, task_str)):
            if rr == 0:
                continue
            cols = row.findAll('td')
            if not len(cols):
                continue

            name = ''
            if cols[cns['aka']].contents:
                for rawaka in str(cols[cns['aka']].contents[0]).split(','):
                    aka = rawaka.strip()
                    if is_number(aka.strip('?')):
                        aka = 'SN' + aka.strip('?') + 'A'
                        oldname = aka
                        name = catalog.add_entry(aka)
                    elif len(aka) == 4 and is_number(aka[:4]):
                        aka = 'SN' + aka
                        oldname = aka
                        name = catalog.add_entry(aka)

            ra = str(cols[cns['ra']].contents[0]).strip()
            dec = str(cols[cns['dec']].contents[0]).strip()

            sn = re.sub('<[^<]+?>', '',
                        str(cols[cns['name']].contents[0])).strip()
            if is_number(sn.strip('?')):
                sn = 'SN' + sn.strip('?') + 'A'
            elif len(sn) == 4 and is_number(sn[:4]):
                sn = 'SN' + sn
            if not name:
                if not sn or sn in ['Transient']:
                    continue
                if sn[:8] == 'MASTER J':
                    sn = sn.replace('MASTER J', 'MASTER OT J').replace(
                        'SNHunt', 'SNhunt')
                if 'POSSIBLE' in sn.upper() and ra and dec:
                    sn = 'PSN J' + ra.replace(':', '').replace('.', '')
                    sn += dec.replace(':', '').replace('.', '')
                oldname = sn
                name = catalog.add_entry(sn)
            sec_source = catalog.entries[name].add_source(
                name=sec_ref, url=sec_refurl, secondary=True)
            sources = []
            if 'ref' in cns:
                reftag = reference = cols[cns['ref']].findAll('a')
                if len(reftag):
                    reference = reftag[0].contents[0].strip()
                    refurl = reftag[0]['href'].strip()
                    sources.append(catalog.entries[name].add_source(
                        name=reference, url=refurl))
            sources.append(sec_source)
            sources = uniq_cdl(list(filter(None, sources)))
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, oldname,
                                               sources)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, sn, sources)

            if cols[cns['aka']].contents:
                for rawaka in str(cols[cns['aka']].contents[0]).split(','):
                    aka = rawaka.strip()
                    if aka == 'SNR G1.9+0.3':
                        aka = 'G001.9+00.3'
                    if aka[:4] == 'PS1 ':
                        aka = 'PS1-' + aka[4:]
                    if aka[:8] == 'MASTER J':
                        aka = aka.replace('MASTER J', 'MASTER OT J').replace(
                            'SNHunt', 'SNhunt')
                    if 'POSSIBLE' in aka.upper() and ra and dec:
                        aka = 'PSN J' + ra.replace(':', '').replace('.', '')
                        aka += dec.replace(':', '').replace('.', '')
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, aka,
                                                       sources)

            if str(cols[cns['type']].contents[0]).strip() != 'unk':
                type = str(cols[cns['type']].contents[0]).strip(' :,')
                catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                   type, sources)
            if (len(cols[cns['host']].contents) > 0 and
                    str(cols[cns['host']].contents[0]).strip() != 'anonymous'):
                catalog.entries[name].add_quantity(
                    SUPERNOVA.HOST,
                    str(cols[cns['host']].contents[0]).strip(), sources)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, sources)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec, sources)
            discstr = str(cols[cns['disc']].contents[0]).strip()
            if discstr and discstr not in baddates:
                if '/' not in discstr:
                    astrot = astrotime(float(discstr), format='jd').datetime
                    ddate = make_date_string(astrot.year, astrot.month,
                                             astrot.day)
                else:
                    ddate = discstr
                catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE,
                                                   ddate, sources)
            maxstr = str(cols[cns.get('max', '')].contents[0]).strip()
            if maxstr and maxstr not in baddates:
                try:
                    if '/' not in maxstr:
                        astrot = astrotime(float(maxstr), format='jd')
                    else:
                        astrot = astrotime(
                            maxstr.replace('/', '-'), format='iso')
                except:
                    catalog.log.info(
                        'Max date conversion failed for `{}`.'.format(maxstr))
                if ((float(str(cols[cns['mmag']].contents[0]).strip()) <= 90.0
                     and
                     not any('GRB' in xx
                             for xx in catalog.entries[name].get_aliases()))):
                    mag = str(cols[cns['mmag']].contents[0]).strip()
                    catalog.entries[name].add_photometry(
                        time=str(astrot.mjd),
                        u_time='MJD',
                        magnitude=mag,
                        source=sources)
            if 'z' in cns and cols[cns['z']].contents[0] != 'n/a':
                catalog.entries[name].add_quantity(
                    SUPERNOVA.REDSHIFT,
                    str(cols[cns['z']].contents[0]).strip(), sources)
            if 'zh' in cns:
                zhost = str(cols[cns['zh']].contents[0]).strip()
                if is_number(zhost):
                    catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT,
                                                       zhost, sources)
            if 'dver' in cns:
                catalog.entries[name].add_quantity(
                    SUPERNOVA.DISCOVERER,
                    str(cols[cns['dver']].contents[0]).strip(), sources)
            if catalog.args.update:
                catalog.journal_entries()
            loopcnt = loopcnt + 1
            if (catalog.args.travis and
                    loopcnt % catalog.TRAVIS_QUERY_LIMIT == 0):
                break

    if not catalog.args.update:
        vsnetfiles = ['latestsne.dat']
        for vsnetfile in vsnetfiles:
            file_name = os.path.join(catalog.get_current_task_repo(),
                                     "" + vsnetfile)
            with open(file_name, 'r', encoding='latin1') as csv_file:
                tsvin = csv.reader(
                    csv_file, delimiter=' ', skipinitialspace=True)
                loopcnt = 0
                for rr, row in enumerate(tsvin):
                    if (not row or row[0] in ['Transient'] or
                            row[0][:4] in ['http', 'www.'] or len(row) < 3):
                        continue
                    name = row[0].strip()
                    if name[:4].isdigit():
                        name = 'SN' + name
                    if name.startswith('PSNJ'):
                        name = 'PSN J' + name[4:]
                    if name.startswith('MASTEROTJ'):
                        name = name.replace('MASTEROTJ', 'MASTER OT J')
                    name = catalog.add_entry(name)
                    sec_source = catalog.entries[name].add_source(
                        name=sec_ref, url=sec_refurl, secondary=True)
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name,
                                                       sec_source)

                    if not is_number(row[1]):
                        continue
                    year = row[1][:4]
                    month = row[1][4:6]
                    day = row[1][6:]
                    if '.' not in day:
                        day = day[:2] + '.' + day[2:]
                    mjd = astrotime(year + '-' + month + '-' + str(
                        floor(float(day))).zfill(2)).mjd
                    mjd += float(day) - floor(float(day))
                    magnitude = row[2].rstrip(ascii_letters)
                    if not is_number(magnitude):
                        continue
                    if magnitude.isdigit():
                        if int(magnitude) > 100:
                            magnitude = magnitude[:2] + '.' + magnitude[2:]

                    if float(str(cols[8].contents[0]).strip()) >= 90.0:
                        continue

                    if len(row) >= 4:
                        if is_number(row[3]):
                            e_magnitude = row[3]
                            refind = 4
                        else:
                            e_magnitude = ''
                            refind = 3

                        if refind >= len(row):
                            sources = sec_source
                        else:
                            reference = ' '.join(row[refind:])
                            source = catalog.entries[name].add_source(
                                name=reference)
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.ALIAS, name, sec_source)
                            sources = uniq_cdl([source, sec_source])
                    else:
                        sources = sec_source

                    band = row[2].lstrip('1234567890.')

                    catalog.entries[name].add_photometry(
                        time=mjd,
                        u_time='MJD',
                        band=band,
                        magnitude=magnitude,
                        e_magnitude=e_magnitude,
                        source=sources)

                    if (catalog.args.travis and
                            loopcnt % catalog.TRAVIS_QUERY_LIMIT == 0):
                        break

    catalog.journal_entries()
    return

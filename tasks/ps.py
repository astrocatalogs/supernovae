"""Import tasks for Pan-STARRS.
"""
import csv
import json
import os
import urllib
import warnings
from glob import glob

import requests
from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import is_number, make_date_string, pbar, uniq_cdl
from astropy.time import Time as astrotime
from bs4 import BeautifulSoup

from ..supernova import SUPERNOVA


def do_ps_mds(catalog):
    task_str = catalog.get_current_task_str()
    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'MDS/apj506838t1_mrt.txt')) as f:
        for ri, row in enumerate(pbar(f.read().splitlines(), task_str)):
            if ri < 35:
                continue
            cols = [x.strip() for x in row.split(',')]
            name = catalog.add_entry(cols[0])
            source = catalog.entries[name].add_source(
                bibcode='2015ApJ...799..208S')
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, cols[2], source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, cols[3], source)
            astrot = astrotime(float(cols[4]), format='mjd').datetime
            ddate = make_date_string(astrot.year, astrot.month, astrot.day)
            catalog.entries[name].add_quantity(SUPERNOVA.DISCOVER_DATE, ddate,
                                               source)
            catalog.entries[name].add_quantity(
                SUPERNOVA.REDSHIFT, cols[5], source, kind='spectroscopic')
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, 'II P',
                                               source)
    catalog.journal_entries()
    return


def do_ps_alerts(catalog):
    task_str = catalog.get_current_task_str()
    alertstables = ['alertstable-2010', 'alertstable-2011', 'alertstable']
    rows = []
    for at in alertstables:
        with open(
                os.path.join(catalog.get_current_task_repo(), 'ps1-clean',
                             at)) as f:
            rows.extend(
                list(csv.reader(
                    f, delimiter=' ', skipinitialspace=True))[1:])
    alertfiles = glob(
        os.path.join(catalog.get_current_task_repo(), 'ps1-clean/*.dat'))
    alertfilestag = dict(
        [(x.split('/')[-1].split('.')[0], x) for x in alertfiles])
    alertfilesid = dict([(x.split('/')[-1].split('.')[0].split('-')[-1], x)
                         for x in alertfiles])
    with open(
            os.path.join(catalog.get_current_task_repo(),
                         'ps1-clean/whitelist')) as f:
        whitelist = list(csv.reader(f, delimiter=' ', skipinitialspace=True))
    wlnames = [x[0] for x in whitelist]
    wlnamesleft = list(wlnames)
    wlra = [x[1] for x in whitelist]
    missing_confirmed = []
    # already_collected = []
    for ri, row in enumerate(pbar(rows, task_str)):
        psname = row[50]
        if psname == '-':
            if row[4] in wlra:
                psname = wlnames[wlra.index(row[4])]
            else:
                continue
        sntype = row[21].replace('SN', '')
        skip_photo = False
        if psname not in wlnamesleft:
            if row[1] == 'confirmed':
                missing_confirmed.append((psname, row[21]))
                # if 'II' in sntype:
                #     pass
                # elif (sntype != 'Ia' or
                #         not (psname.startswith(('PS1-12', 'PS1-13')) or
                #              (psname.startswith('PS1-10') and
                #              len(psname.replace('PS1-10', '')) == 3 and
                #              psname[-3:] > 'ams'))):
                #     if sntype == 'Ia' and psname.startswith('PS1-10'):
                #         already_collected.append((psname, row[21]))
                #     else:
                #         missing_confirmed.append((psname, row[21]))
                skip_photo = True
            else:
                continue
        if psname in wlnamesleft:
            wlnamesleft.remove(psname)

        name, source = catalog.new_entry(
            psname,
            srcname='Pan-STARRS Alerts',
            url='http://telescopes.rc.fas.harvard.edu/ps1/')

        catalog.entries[name].add_quantity(SUPERNOVA.RA, row[4], source)
        catalog.entries[name].add_quantity(SUPERNOVA.DEC, row[5], source)
        if sntype != '-':
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, sntype,
                                               source)
        if row[22] != '-':
            catalog.entries[name].add_quantity(SUPERNOVA.REDSHIFT, row[22],
                                               source)
        # Disabling photometry import
        continue

        if skip_photo:
            continue
        psinternal = row[-1].split('.')[0]
        if not is_number(psinternal.split('-')[0]):
            psid = row[0].zfill(6)
            if psid not in alertfilesid:
                continue
            pspath = alertfilesid[psid]
        else:
            if psinternal not in alertfilestag:
                continue
            pspath = alertfilestag[psinternal]
        with open(pspath) as f:
            photrows = list(
                csv.reader(
                    f, delimiter=' ', skipinitialspace=True))
        for pi, prow in enumerate(photrows):
            if pi == 0 or prow[3] == '-':
                continue
            counts = prow[13]
            e_counts = prow[14]
            photodict = {
                PHOTOMETRY.TIME: prow[1],
                PHOTOMETRY.U_TIME: 'MJD',
                PHOTOMETRY.BAND: prow[2],
                PHOTOMETRY.MAGNITUDE: prow[3],
                PHOTOMETRY.E_MAGNITUDE: prow[4],
                PHOTOMETRY.COUNT_RATE: counts,
                PHOTOMETRY.E_COUNT_RATE: e_counts,
                PHOTOMETRY.ZERO_POINT: prow[15],
                PHOTOMETRY.INSTRUMENT: 'GPC1',
                PHOTOMETRY.OBSERVATORY: 'PS1',
                PHOTOMETRY.SURVEY: 'MDS',
                PHOTOMETRY.TELESCOPE: 'PS1',
                PHOTOMETRY.SYSTEM: 'PS1',
                PHOTOMETRY.SOURCE: source
            }
            ul_sigma = 3.0
            if float(counts) < ul_sigma * float(e_counts):
                photodict[PHOTOMETRY.UPPER_LIMIT] = True
                photodict[PHOTOMETRY.UPPER_LIMIT_SIGMA] = ul_sigma
            catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()
    # print(already_collected)
    # print(missing_confirmed)
    return


def do_ps_threepi(catalog):
    """Import data from Pan-STARRS' 3pi page."""
    task_str = catalog.get_current_task_str()
    teles = 'Pan-STARRS1'
    fname = os.path.join(catalog.get_current_task_repo(), '3pi/page00.html')
    ps_url = ("http://psweb.mp.qub.ac.uk/"
              "ps1threepi/psdb/public/?page=1&sort=followup_flag_date")
    html = catalog.load_url(ps_url, fname, write=False)
    if not html:
        return

    # Clean some common HTML manglings
    html = html.replace('ahref=', 'a href=')

    bs = BeautifulSoup(html, 'html5lib')
    div = bs.find('div', {'class': 'pagination'})
    offline = False
    if not div:
        offline = True
    else:
        links = div.findAll('a')
        if not links:
            offline = True

    if offline:
        if catalog.args.update:
            return
        warnings.warn('Pan-STARRS 3pi offline, using local files only.')
        with open(fname, 'r') as f:
            html = f.read()
        bs = BeautifulSoup(html, 'html5lib')
        div = bs.find('div', {'class': 'pagination'})
        links = div.findAll('a')
    else:
        with open(fname, 'w') as f:
            f.write(html)

    numpages = int(links[-2].contents[0])
    oldnumpages = len(
        glob(os.path.join(catalog.get_current_task_repo(), '3pi/page*')))
    for page in pbar(range(1, numpages), task_str):
        fname = os.path.join(catalog.get_current_task_repo(), '3pi/page') + \
            str(page).zfill(2) + '.html'
        if offline:
            if not os.path.isfile(fname):
                continue
            with open(fname, 'r') as f:
                html = f.read()
        else:
            if (catalog.current_task.load_archive(catalog.args) and
                    page < oldnumpages and os.path.isfile(fname)):
                with open(fname, 'r') as f:
                    html = f.read()
            else:
                response = urllib.request.urlopen(
                    "http://psweb.mp.qub.ac.uk/ps1threepi/psdb/public/?page=" +
                    str(page) + "&sort=followup_flag_date")
                with open(fname, 'w') as f:
                    html = response.read().decode('utf-8')
                    f.write(html)

        bs = BeautifulSoup(html, 'html5lib')
        trs = bs.findAll('tr')
        for tr in pbar(trs, task_str):
            tds = tr.findAll('td')
            if not tds:
                continue
            refs = []
            aliases = []
            ttype = ''
            ctype = ''
            for tdi, td in enumerate(tds):
                if tdi == 0:
                    psname = td.contents[0]
                    pslink = psname['href']
                    psname = psname.text
                elif tdi == 1:
                    ra = td.contents[0]
                elif tdi == 2:
                    dec = td.contents[0]
                elif tdi == 3:
                    ttype = td.contents[0]
                    if ttype != 'sn' and ttype != 'orphan':
                        break
                elif tdi == 6:
                    if not td.contents:
                        continue
                    ctype = td.contents[0]
                    if ctype == 'Observed':
                        ctype = ''
                elif tdi == 17:
                    if td.contents:
                        crossrefs = td.findAll('a')
                        for cref in crossrefs:
                            if 'atel' in cref.contents[0].lower():
                                refs.append([cref.contents[0], cref['href']])
                            elif is_number(cref.contents[0][:4]):
                                continue
                            else:
                                aliases.append(cref.contents[0])

            if ttype != 'sn' and ttype != 'orphan':
                continue

            name = ''
            for alias in aliases:
                if alias[:2] == 'SN':
                    name = alias
            if not name:
                name = psname
            name = catalog.add_entry(name)
            sources = [
                catalog.entries[name].add_source(
                    name='Pan-STARRS 3Pi',
                    url=('http://psweb.mp.qub.ac.uk/'
                         'ps1threepi/psdb/'))
            ]
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name,
                                               sources[0])
            for ref in refs:
                sources.append(catalog.entries[name].add_source(
                    name=ref[0], url=ref[1]))
            source = uniq_cdl(sources)
            for alias in aliases:
                newalias = alias
                if alias[:3] in ['CSS', 'SSS', 'MLS']:
                    newalias = alias.replace('-', ':', 1)
                newalias = newalias.replace('PSNJ', 'PSN J')
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, newalias,
                                                   source)
            catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, source)
            catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec, source)
            catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE, ctype,
                                               source)

            fname2 = os.path.join(catalog.get_current_task_repo(),
                                  '3pi/candidate-')
            fname2 += pslink.rstrip('/').split('/')[-1] + '.html'
            if offline:
                if not os.path.isfile(fname2):
                    continue
                with open(fname2, 'r') as f:
                    html2 = f.read()
            else:
                if (catalog.current_task.load_archive(catalog.args) and
                        os.path.isfile(fname2)):
                    with open(fname2, 'r') as f:
                        html2 = f.read()
                else:
                    pslink = ('http://psweb.mp.qub.ac.uk/'
                              'ps1threepi/psdb/public/') + pslink
                    try:
                        session2 = requests.Session()
                        response2 = session2.get(pslink)
                    except Exception:
                        offline = True
                        if not os.path.isfile(fname2):
                            continue
                        with open(fname2, 'r') as f:
                            html2 = f.read()
                    else:
                        html2 = response2.text
                        with open(fname2, 'w') as f:
                            f.write(html2)

            bs2 = BeautifulSoup(html2, 'html5lib')
            scripts = bs2.findAll('script')
            nslines = []
            nslabels = []
            for script in scripts:
                if 'jslcdata.push' not in script.text:
                    continue
                slines = script.text.splitlines()
                for line in slines:
                    if 'jslcdata.push' in line:
                        json_fname = (line.strip()
                                      .replace('jslcdata.push(', '')
                                      .replace(');', ''))
                        nslines.append(json.loads(json_fname))
                    if ('jslabels.push' in line and 'blanks' not in line and
                            'non det' not in line):
                        json_fname = (line.strip()
                                      .replace('jslabels.push(', '')
                                      .replace(');', ''))
                        nslabels.append(json.loads(json_fname)['label'])
            for li, line in enumerate(nslines[:len(nslabels)]):
                if not line:
                    continue
                for obs in line:
                    catalog.entries[name].add_photometry(
                        time=str(obs[0]),
                        u_time='MJD',
                        band=nslabels[li],
                        instrument='GPC',
                        magnitude=str(obs[1]),
                        e_magnitude=str(obs[2]),
                        source=source,
                        telescope=teles)
            # Ignoring upper limits as they are usually spurious chip gaps.
            # for li, line in enumerate(nslines[2 * len(nslabels):]):
            #     if not line:
            #         continue
            #     for obs in line:
            #         catalog.entries[name].add_photometry(
            #             time=str(obs[0]),
            #             u_time='MJD',
            #             band=nslabels[li],
            #             instrument='GPC',
            #             magnitude=str(obs[1]),
            #             upperlimit=True,
            #             source=source,
            #             telescope=teles)
            assoctab = bs2.find('table', {'class': 'generictable'})
            hostname = ''
            redshift = ''
            if assoctab:
                trs = assoctab.findAll('tr')
                headertds = [x.contents[0] for x in trs[1].findAll('td')]
                tds = trs[1].findAll('td')
                for tdi, td in enumerate(tds):
                    if tdi == 1:
                        hostname = td.contents[0].strip()
                    elif tdi == 4:
                        if 'z' in headertds:
                            redshift = td.contents[0].strip()
            # Skip galaxies with just SDSS id
            if is_number(hostname):
                continue
            catalog.entries[name].add_quantity(SUPERNOVA.HOST, hostname,
                                               source)
            if redshift:
                catalog.entries[name].add_quantity(
                    [SUPERNOVA.REDSHIFT, SUPERNOVA.HOST_REDSHIFT],
                    redshift,
                    source,
                    kind='host')
            if catalog.args.update:
                catalog.journal_entries()

        catalog.journal_entries()
        # Only run first page for Travis
        if catalog.args.travis:
            break

    return

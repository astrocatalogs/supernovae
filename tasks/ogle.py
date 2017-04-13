"""Import tasks for OGLE.
"""
import os
import re

from astrocats.catalog.utils import is_number, jd_to_mjd, pbar, uniq_cdl
from bs4 import BeautifulSoup, NavigableString, Tag

from decimal import Decimal

from ..supernova import SUPERNOVA


def do_ogle(catalog):
    task_str = catalog.get_current_task_str()
    basenames = [
        'transients', 'transients/2015', 'transients/2014b', 'transients/2014',
        'transients/2013', 'transients/2012'
    ]
    oglenames = []
    ogleupdate = [True, False, False, False, False]
    for b, bn in enumerate(pbar(basenames, task_str)):
        if catalog.args.update and not ogleupdate[b]:
            continue

        filepath = os.path.join(catalog.get_current_task_repo(), 'OGLE-')
        filepath += bn.replace('/', '-') + '-transients.html'
        htmltxt = catalog.load_url(
            'http://ogle.astrouw.edu.pl/ogle4/' + bn + '/transients.html',
            filepath)
        if not htmltxt:
            continue

        soup = BeautifulSoup(htmltxt, 'html5lib')
        links = soup.findAll('a')
        breaks = soup.findAll('br')
        datalinks = []
        datafnames = []
        for a in links:
            if a.has_attr('href'):
                if '.dat' in a['href']:
                    datalinks.append('http://ogle.astrouw.edu.pl/ogle4/' + bn +
                                     '/' + a['href'])
                    datafnames.append(
                        bn.replace('/', '-') + '-' + a['href'].replace('/',
                                                                       '-'))

        ec = -1
        reference = 'OGLE-IV Transient Detection System'
        refurl = 'http://ogle.astrouw.edu.pl/ogle4/transients/transients.html'
        for bi, br in enumerate(pbar(breaks, task_str)):
            sibling = br.nextSibling
            if 'Ra,Dec=' in sibling:
                line = sibling.replace('\n', '').split('Ra,Dec=')
                name = line[0].strip()
                ec += 1

                if 'NOVA' in name or 'dupl' in name:
                    continue

                if name in oglenames:
                    continue
                oglenames.append(name)

                name = catalog.add_entry(name)

                mySibling = sibling.nextSibling
                atelref = ''
                claimedtype = ''
                while 'Ra,Dec=' not in mySibling:
                    if isinstance(mySibling, NavigableString):
                        if not claimedtype and 'class=' in str(mySibling):
                            claimedtype = re.sub(r'\([^)]*\)', '',
                                                 str(mySibling).split('=')[-1])
                            claimedtype = claimedtype.replace('SN', '').strip()
                            if claimedtype == '-':
                                claimedtype = ''
                    if isinstance(mySibling, Tag):
                        atela = mySibling
                        if (atela and atela.has_attr('href') and
                                'astronomerstelegram' in atela['href']):
                            atelref = atela.contents[0].strip()
                            atelurl = atela['href']
                    mySibling = mySibling.nextSibling
                    if mySibling is None:
                        break

                # nextSibling = sibling.nextSibling
                # if ((isinstance(nextSibling, Tag) and
                #      nextSibling.has_attr('alt') and
                #      nextSibling.contents[0].strip() != 'NED')):
                #     radec = nextSibling.contents[0].strip().split()
                # else:
                #     radec = line[-1].split()
                # ra = radec[0]
                # dec = radec[1]

                fname = os.path.join(catalog.get_current_task_repo(),
                                     'OGLE/') + datafnames[ec]
                csvtxt = catalog.load_url(datalinks[ec], fname)

                lcdat = csvtxt.splitlines()
                sources = [
                    catalog.entries[name].add_source(
                        name=reference, url=refurl)
                ]
                catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name,
                                                   sources[0])
                if atelref and atelref != 'ATel#----':
                    sources.append(catalog.entries[name].add_source(
                        name=atelref, url=atelurl))
                sources = uniq_cdl(sources)

                if name.startswith('OGLE'):
                    if name[4] == '-':
                        if is_number(name[5:9]):
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.DISCOVER_DATE, name[5:9], sources)
                    else:
                        if is_number(name[4:6]):
                            catalog.entries[name].add_quantity(
                                SUPERNOVA.DISCOVER_DATE, '20' + name[4:6],
                                sources)

                # RA and Dec from OGLE pages currently not reliable
                # catalog.entries[name].add_quantity(SUPERNOVA.RA, ra, sources)
                # catalog.entries[name].add_quantity(SUPERNOVA.DEC, dec,
                # sources)
                if claimedtype and claimedtype != '-':
                    catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                       claimedtype, sources)
                elif ('SN' not in name and
                      SUPERNOVA.CLAIMED_TYPE not in catalog.entries[name]):
                    catalog.entries[name].add_quantity(SUPERNOVA.CLAIMED_TYPE,
                                                       'Candidate', sources)
                for row in lcdat:
                    row = row.split()
                    mjd = str(jd_to_mjd(Decimal(row[0])))
                    magnitude = row[1]
                    if float(magnitude) > 90.0:
                        continue
                    e_mag = row[2]
                    upperlimit = False
                    if e_mag == '-1' or float(e_mag) > 10.0:
                        e_mag = ''
                        upperlimit = True
                    catalog.entries[name].add_photometry(
                        time=mjd,
                        u_time='MJD',
                        band='I',
                        magnitude=magnitude,
                        e_magnitude=e_mag,
                        system='Vega',
                        source=sources,
                        upperlimit=upperlimit)
                if catalog.args.update:
                    catalog.journal_entries()
                if catalog.args.travis and bi >= catalog.TRAVIS_QUERY_LIMIT:
                    break

        catalog.journal_entries()
    return

"""Import tasks for data directly donated to the Open Supernova Catalog.
"""
import os
from glob import glob
from html import unescape

from bs4 import BeautifulSoup

from astrocats.catalog.photometry import PHOTOMETRY
from astrocats.catalog.utils import pbar


def do_sousa(catalog):
    task_str = catalog.get_current_task_str()

    html = catalog.load_url(
        'http://people.physics.tamu.edu/pbrown/SwiftSN/swift_sn.html',
        os.path.join(catalog.get_current_task_repo(), 'SOUSA/swift_sn.html'))

    soup = BeautifulSoup(html, 'html5lib')
    links = soup.body.findAll("a")
    for link in pbar(links, task_str + ': links'):
        try:
            link['href']
        except KeyError:
            continue
        if '.dat' in link['href']:
            ulink = unescape(link['href']).replace('\n', '')
            catalog.load_url(ulink,
                             os.path.join(catalog.get_current_task_repo(),
                                          'SOUSA/') + ulink.split('/')[-1])

    files = glob(os.path.join(catalog.get_current_task_repo(), 'SOUSA/*.dat'))
    namereps = {
        'CSS140914': 'CSS140914:010107-101840'
    }
    for fi in pbar(files, task_str):
        name = os.path.basename(fi).split('_')[0]
        if name in namereps:
            name = namereps[name]
        name, source = catalog.new_entry(
            name,
            srcname='SOUSA',
            bibcode='2014Ap&SS.354...89B',
            url='http://people.physics.tamu.edu/pbrown/SwiftSN/swift_sn.html')
        with open(fi, 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                if not line.strip() or line[0] == '#':
                    continue
                cols = list(filter(None, line.split()))
                band = cols[0]
                mjd = cols[1]
                # Skip lower limit entries for now
                if cols[2] == 'NULL' and cols[6] == 'NULL':
                    continue
                isupp = cols[2] == 'NULL' and cols[6] != 'NULL'
                mag = cols[2] if not isupp else cols[4]
                e_mag = cols[3] if not isupp else ''
                upp = '' if not isupp else True
                photodict = {
                    PHOTOMETRY.TIME: mjd,
                    PHOTOMETRY.U_TIME: 'MJD',
                    PHOTOMETRY.MAGNITUDE: mag,
                    PHOTOMETRY.UPPER_LIMIT: upp,
                    PHOTOMETRY.BAND: band,
                    PHOTOMETRY.SOURCE: source,
                    PHOTOMETRY.TELESCOPE: 'Swift',
                    PHOTOMETRY.INSTRUMENT: 'UVOT',
                    PHOTOMETRY.SYSTEM: 'Vega'
                }
                if e_mag:
                    photodict[PHOTOMETRY.E_MAGNITUDE] = e_mag
                catalog.entries[name].add_photometry(**photodict)
    catalog.journal_entries()

    return

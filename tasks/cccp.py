"""General data import tasks.
"""
import csv
import os
from glob import glob

from bs4 import BeautifulSoup

from astrocats.utils import pbar
from astrocats.structures.struct import PHOTOMETRY
from decimal import Decimal

from ..supernova import SUPERNOVA

WEIZ_URL = 'https://webhome.weizmann.ac.il/home/iair/sc_cccp.html'


def do_cccp(catalog):
    task_str = catalog.get_current_task_str()
    cccpbands = ['B', 'V', 'R', 'I']
    file_names = list(glob(os.path.join(catalog.get_current_task_repo(), 'CCCP/apj407397*.txt')))
    for datafile in pbar(file_names, task_str + ': apj407397...', sort=True):
        with open(datafile, 'r') as ff:
            tsvin = csv.reader(ff, delimiter='\t', skipinitialspace=True)
            for rr, row in enumerate(tsvin):
                if rr == 0:
                    continue
                elif rr == 1:
                    name = 'SN' + row[0].split('SN ')[-1]
                    name = catalog.add_entry(name)
                    source = catalog.entries[name].add_source(bibcode='2012ApJ...744...10K')
                    catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)
                elif rr >= 5:
                    mjd = str(Decimal(row[0]) + 53000)
                    for bb, band in enumerate(cccpbands):
                        if row[2 * bb + 1]:
                            mag = row[2 * bb + 1].strip('>')
                            upl = (not row[2 * bb + 2])
                            photo = {
                                PHOTOMETRY.TIME: mjd,
                                PHOTOMETRY.U_TIME: 'MJD',
                                PHOTOMETRY.BAND: band,
                                PHOTOMETRY.MAGNITUDE: mag,
                                PHOTOMETRY.UPPERLIMIT: upl,
                                PHOTOMETRY.SOURCE: source
                            }
                            e_mag = row[2 * bb + 2]
                            if len(e_mag) > 0:
                                photo[PHOTOMETRY.E_MAGNITUDE] = e_mag

                            catalog.entries[name].add_photometry(**photo)

    html = catalog.load_url(
        WEIZ_URL, os.path.join(catalog.get_current_task_repo(), 'CCCP/sc_cccp.html'))

    soup = BeautifulSoup(html, 'html5lib')
    links = soup.body.findAll("a")
    path = os.path.join(catalog.get_current_task_repo(), 'CCCP/')
    for link in pbar(links, task_str + ': links'):
        if 'sc_sn' in link['href']:
            name = catalog.add_entry(link.text.replace(' ', ''))
            source = catalog.entries[name].add_source(name='CCCP', url=WEIZ_URL)
            catalog.entries[name].add_quantity(SUPERNOVA.ALIAS, name, source)

            html2 = catalog.load_url(
                'https://webhome.weizmann.ac.il/home/iair/' + link['href'],
                path + link['href'].split('/')[-1])

            soup2 = BeautifulSoup(html2, 'html5lib')
            links2 = soup2.body.findAll("a")
            for link2 in links2:
                if '.txt' in link2['href'] and '_' in link2['href']:
                    band = link2['href'].split('_')[1].split('.')[0].upper()

                    # Many 404s in photometry, set cache_only = True unless
                    # attempting complete rebuild.
                    html3 = catalog.load_url(
                        'https://webhome.weizmann.ac.il/home/iair/cccp/' + link2['href'],
                        path + link2['href'].split('/')[-1], cache_only=True)

                    if html3 is None:
                        continue

                    table = [[str(Decimal(yy.strip())).rstrip('0') for yy in xx.split(',')]
                             for xx in list(filter(None, html3.split('\n')))]
                    for row in table:
                        catalog.entries[name].add_photometry(
                            time=str(Decimal(row[0]) + 53000),
                            u_time='MJD', band=band, magnitude=row[1],
                            e_magnitude=row[2], source=source)

    catalog.journal_entries()
    return
